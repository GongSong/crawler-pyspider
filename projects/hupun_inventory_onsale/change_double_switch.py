from gevent import monkey
monkey.patch_all()
import time
from hupun_inventory_onsale.es.auto_shelf_switch import EsAutoShelfSwitch
from hupun_inventory_onsale.page.inventory_sync_upload import InventorySyncUpload
from hupun_inventory_onsale.page.inverntory_sync_config import InventorySyncConfig
from mq_handler.base import Base
from pyspider.helper.date import Date
import threading
from pyspider.helper.channel import erp_name_to_shopuid
from hupun_inventory_onsale.on_shelf_config import *
import traceback
from pyspider.helper.utils import generator_list, progress_counter
from pyspider.helper.retry import Retry
from alarm.page.ding_talk import DingTalk
from hupun_inventory_onsale.es.double_switch_status import EsDoubleSwitchStatus
import queue
from pyspider.core.model.storage import ai_storage_redis
import random


class ChangeDoubleSwitch(Base):
    '''
    操作erp库存商品【上传库存】和【自动上架】设置,0为关，1为开
    '''
    max_threads = 4

    def execute(self):
        print('开始设置商品【上传库存】及【自动上架】开关')
        self.print_basic_info()
        data = self._data

        total_amount = data.get('total')
        missions_amount = data.get('taskNum')
        mission = 'spu_switch_mission'
        status = 'spu_switch_status'
        progress = 'spu_switch_progress'
        total = 'spu_switch_total'
        ai_storage_redis.set(total, total_amount)

        q = queue.Queue(self.max_threads)
        save_list = []
        for index, items in enumerate(data.get('list', [])):
            spu_barcode = items.get('spuBarcode')
            for channel in items.get('channels', []):
                es_data = {
                    "spuBarcode": spu_barcode,
                    "channel": channel,
                    "syncStatus": '同步中',
                    # 对比操作时间，同步最近一天的数据
                    "syncTime": str(Date.now().millisecond()),
                }
                save_list.append(es_data)

        for _list in generator_list(save_list, 200):
            EsDoubleSwitchStatus().update(_list)

        for items in data.get('list'):
            spu_barcode = items.get('spuBarcode')
            target_status = self.translate_target_status(items)
            for channel in items.get('channels'):
                q.put(1)
                t = threading.Thread(target=self.consume_task, args=(target_status,spu_barcode,channel,items,q))
                t.start()
        q.join()
        time.sleep(1)

        self.handle_progress_para(missions_amount, mission, status, progress, total)

    @progress_counter('spu_switch_progress')
    def consume_task(self, target_status,spu_barcode,channel,items,queue):
        print(Date.now().format(), '开始消费：', items, channel)
        error_msg = ''
        es_data = {
            "spuBarcode": spu_barcode,
            "channel": channel,
        }

        try:
            if target_status == 'other':
                error_msg = '双开关设置有问题，请确认传入开关状态'
                raise Exception('双开关设置有问题，请确认传入开关状态')
            shop_uid = erp_name_to_shopuid(channel)
            if shop_uid == 'other':
                error_msg = 'erp查询渠道出现错误，请确认传入商品渠道信息'
                # 需处理异常
                raise Exception('查询渠道{0} 出现错误，请确认传入商品渠道信息'.format(channel))
            elif REDBOOK_SHOPNAME in channel:
                outer_title = items.get('name')
                if not outer_title:
                    error_msg = '小红书商品未传入中文名，无法查询'
                    raise Exception('小红书商品未传入中文名，请确认传入参数')
                outer_title = outer_title.strip()
                outer_product_id = 'HS' + items.get('goodsId')
                # 小红书渠道用小红书的商品名作为搜索输入，且必须有小红书的barcode，即outer_product_id
                erp_result = self.change_erp_status(outer_title, shop_uid, target_status, error_msg, outer_product_id)
                erp_result_handle = erp_result[0] if type(erp_result) == tuple else erp_result
                if erp_result_handle is True:
                    print('商品：{0} erp同步操作成功'.format(outer_title))
                    self.save_erp_switch_es(items, channel, target_status, erp_result[1])
                    self.success_save_es(es_data)
                else:
                    error_msg = erp_result[1]
                    print('商品：{0} erp同步操作失败'.format(outer_title))
                    if not error_msg:
                        error_msg = 'erp同步失败后重试导致的失败'
                    self.error_save_es(es_data, error_msg)
            else:
                erp_result = self.change_erp_status(spu_barcode, shop_uid, target_status, error_msg)
                erp_result_handle = erp_result[0] if type(erp_result) == tuple else erp_result
                if erp_result_handle is True:
                    print('商品：{0} erp同步操作成功'.format(spu_barcode))
                    self.save_erp_switch_es(items, channel, target_status, erp_result[1])
                    self.success_save_es(es_data)
                else:
                    error_msg = erp_result[1]
                    print('商品：{0} erp同步操作失败'.format(spu_barcode))
                    if not error_msg:
                        error_msg = 'erp同步失败后重试导致的失败'
                    self.error_save_es(es_data, error_msg)
        except:
            print('传入数据处理错误，请确认传入数据格式:', items)
            print(traceback.format_exc())
            if not error_msg:
                error_msg = '传入数据处理错误，请确认传入数据格式'
            self.error_save_es(es_data, error_msg)
        finally:
            queue.get()
            queue.task_done()

    @Retry.retry_parameter(5, sleep_time=10)
    def change_erp_status(self, spu_barcode, shop_uid, target_status, error_msg, outer_product_id=''):
        ''' 更改erp中【自动上架】开关 '''
        try:
            cookie_num = random.randint(3, 7)
            search_list = InventorySyncConfig(spu_barcode, shop_uid, outer_product_id).set_cookie_position(
                cookie_num).use_cookie_pool().get_result()
            if search_list == '会话过期':
                error_msg = 'erp登陆会话过期，需等待系统重新登陆erp'
                print('erp登陆会话过期。')
                return False, error_msg
            elif search_list == '查询小红书无outer_product_id':
                error_msg = '小红书渠道erp查询时，必须含有小红书的outer_product_id，请检查传入数据'
                return 'other', error_msg
            elif not search_list:
                error_msg = '在ERP店铺宝贝中找不到该商品。'
                print('{} 在ERP店铺宝贝中找不到该商品。'.format(spu_barcode))
                return 'other', error_msg
            else:
                channel_spucode_list = search_list
                # 遍历查询到的所有商品，如有商品的【自动上架】状态与目标状态不同，则将该商品的状态改为目标状态。
                for search_item in search_list:
                    upload_status = search_item['upload_status']
                    search_item_id = search_item['item_id']
                    if upload_status != target_status:
                        InventorySyncUpload(search_item_id, target_status).set_cookie_position(cookie_num).use_cookie_pool().get_result()
                        time.sleep(0.1)
                # 修改状态完成后，再次查询检测。如仍有与目标状态不同的商品，则返回错误，进行重试。
                # time.sleep(0.5)
                checked_list = InventorySyncConfig(spu_barcode, shop_uid, outer_product_id).set_cookie_position(
                    cookie_num).use_cookie_pool().get_result()
                if checked_list == '会话过期':
                    print('万里牛会话过期')
                    error_msg = '万里牛会话过期，ERP库存同步修改失败。'
                    return False, error_msg

                for check_item in checked_list:
                    _upload_status = check_item['upload_status']
                    if _upload_status != target_status:
                        print('操作未完全成功')
                        error_msg = 'ERP库存同步修改失败。'
                        return False, error_msg
                print('{0}渠道:{1} erp同步上下架状态操作成功'.format(spu_barcode, shop_uid))
                error_msg = ''
                return True, channel_spucode_list
        except Exception:
            print('同步操作失败，失败spu_barcode：{0},channel:{1},target_status:{2}'.
                  format(spu_barcode, shop_uid, target_status))
            print(traceback.format_exc())
            if not error_msg:
                error_msg = 'ERP库存同步修改失败。'
            return False, error_msg

    def translate_target_status(self, data):
        '''将【上传库存】【自动上架】开关的状态转化为万里牛操作所需参数的值'''
        inventory_switch = data.get('inventory_switch')
        shelf_switch = data.get('shelf_switch')
        if inventory_switch == 0:
            return 0
        elif inventory_switch == 1 and shelf_switch == 0:
            return 1
        elif inventory_switch == 1 and shelf_switch == 1:
            return 2
        else:
            return 'other'

    def save_erp_switch_es(self, item, channel, target_status, channel_spucode_list):
        try:
            for channel_spucode in channel_spucode_list:
                if VIP_SHOPNAME in channel:
                    fake_sku = channel_spucode['item_id'].split('|')[-1]
                else:
                    fake_sku = channel_spucode['item_id'][2:]

                save_data = {
                    'fakeSku': fake_sku,
                    'spuBarcode': item['spuBarcode'],
                    'channel': channel,
                    # 'name': item['name'],
                    'switchStatus': '关' if target_status == 0 or target_status == 1 else '开',
                    'inventorySwitchStatus': '关' if target_status == 0 else '开',
                    'syncTime': Date.now().format_es_utc_with_tz(),
                }
                EsAutoShelfSwitch().update([save_data], async=True)
        except Exception:
            print('保存开关状态失败', item)
            print(traceback.format_exc())

    def error_save_es(self, es_data, error_msg):
        '''操作失败时，更新部分字段后存入es'''
        es_data['syncStatus'] = '同步失败'
        es_data['syncTime'] = str(Date.now().millisecond())
        if not error_msg:
            error_msg = '未能被捕捉到到异常错误'
        es_data['failReason'] = error_msg
        EsDoubleSwitchStatus().update([es_data], async=True)
        self.ding_talk_alarm(es_data, error_msg)
        print('保存操作错误成功', es_data)

    def success_save_es(self, es_data):
        '''操作成功时，更新部分字段后存入es'''
        es_data['syncStatus'] = '同步成功'
        es_data['syncTime'] = str(Date.now().millisecond())
        es_data['failReason'] = ''
        EsDoubleSwitchStatus().update([es_data], async=True)
        print('保存成功', es_data)

    @staticmethod
    def ding_talk_alarm(es_data, error_msg):
        token = '87053027d1d9c2ca35b1eda6d248b3d087b764c135f1cb9b1b3387c47322d411'
        title = '万里牛例外宝贝双开关操作报警'
        content = es_data['channel'] + '的商品：' +  es_data['spuBarcode'] + '例外宝贝双开关操作失败，原因：' + error_msg
        DingTalk(token, title, content).enqueue()

    def handle_progress_para(self, missions_amount, mission, status, progress, total):
        '''进度参数的redis设置'''
        if missions_amount > 1:
            ai_storage_redis.incr(mission)
            time.sleep(1)
            shelf_mission = int(ai_storage_redis.get(mission)) if ai_storage_redis.get(mission) else 0
            print('总任务数：', shelf_mission)
            if shelf_mission >= missions_amount:
                ai_storage_redis.set(status, 1)
                ai_storage_redis.set(progress, 0)
                ai_storage_redis.set(total, 0)
                ai_storage_redis.set(mission, 0)
                print(Date.now().format(), '==========完成设置商品【上传库存】及【自动上架】开关==========')

        else:
            ai_storage_redis.set(status, 1)
            ai_storage_redis.set(progress, 0)
            ai_storage_redis.set(total, 0)
            print(Date.now().format(), '==========完成设置商品【上传库存】及【自动上架】开关==========')

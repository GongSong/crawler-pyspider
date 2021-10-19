from gevent import monkey
monkey.patch_all()
import time
import traceback
from hupun_inventory_onsale.page.inventory_sync_upload import InventorySyncUpload
from hupun_inventory_onsale.page.inverntory_sync_config import InventorySyncConfig
from mq_handler.base import Base
from pyspider.helper.date import Date
from pyspider.helper.retry import Retry
import threading
from hupun_slow_crawl.model.es.store_house import StoreHouse
from hupun_inventory_onsale.on_shelf_config import *
from hupun_inventory_onsale.es.inventory_ratio_status import EsInventoryRatioStatus
from alarm.page.ding_talk import DingTalk
import queue
from pyspider.core.model.storage import ai_storage_redis
from hupun_inventory_onsale.es.inventory_ratio import EsInventoryRatio
from pyspider.helper.utils import generator_list, progress_counter
import random


class SyncInventoryRatio(Base):
    """
    同步商品的库存比例
    """
    max_threads = 4

    def execute(self):
        print('开始同步商品spu库存的比例')
        self.print_basic_info()
        data = self._data

        total_amount = data.get('total')
        missions_amount = data.get('taskNum')
        mission = 'spu_set_ratio_mission'
        status = 'spu_set_ratio_status'
        progress = 'spu_set_ratio_progress'
        total = 'spu_set_ratio_total'
        ai_storage_redis.set(total, total_amount)

        q = queue.Queue(self.max_threads)
        save_list = []
        for item in data.get('list'):
            channel = item['channel']
            spu_barcode = item['spuBarcode']
            es_data = {
                "spuBarcode": spu_barcode,
                "channel": channel,
                "syncStatus": '同步中',
                # 对比操作时间，同步最近一天的数据
                "syncTime": str(Date.now().millisecond()),
                "failReason": ""
            }
            save_list.append(es_data)

        for _list in generator_list(save_list, 200):
            EsInventoryRatioStatus().update(_list)

        for item in data.get('list'):
            t = threading.Thread(target=self.consume_task, args=(item, q,))
            q.put(1)
            t.start()
        q.join()
        time.sleep(1)

        self.handle_progress_para(missions_amount, mission, status, progress, total)

    @progress_counter('spu_set_ratio_progress')
    def consume_task(self, item, queue):
        print('开始消费：', item)
        error_msg = ''
        channel = item['channel']
        spu_barcode = item['spuBarcode']
        es_data = {
            "spuBarcode": spu_barcode,
            "channel": channel,
        }
        try:
            quantity_type = item['quantity_type']
            upload_ratio = item['upload_ratio']
            shop_uid = self.erp_shortname_to_shopuid(channel)
            storage_uid = item['storage']
            virtual_inventory = item['virtual_inventory']
            print(shop_uid)
            if shop_uid == 'other':
                print('渠道名异常，请确认传入参数')
                error_msg = '渠道名异常，请确认传入参数'
                raise Exception('渠道名异常，请确认传入参数')
            elif '小红书' in channel:
                outer_title = item.get('name')
                if not outer_title:
                    error_msg = '小红书商品未传入中文名，无法查询'
                    raise Exception('小红书商品无中文名，请确认传入参数')
                outer_title = outer_title.strip()
                outer_product_id = 'HS' + item['outer_product_id']
                erp_result = self.change_erp_status(outer_title, shop_uid, channel, quantity_type, upload_ratio,storage_uid,virtual_inventory,error_msg,outer_product_id)
                erp_result_handle = erp_result[0] if type(erp_result) == tuple else erp_result
                if erp_result_handle is True:
                    print('商品：{0} erp同步库存比例成功'.format(outer_title))
                    self.save_erp_switch_es(channel,item,erp_result[1])
                    self.success_save_es(es_data)
                else:
                    error_msg = erp_result[1]
                    print('商品：{0} erp同步库存比例失败'.format(outer_title))
                    if not error_msg:
                        error_msg = 'erp同步失败后重试导致的失败'
                    self.error_save_es(es_data, error_msg)
            else:
                print(spu_barcode, shop_uid, channel, quantity_type, upload_ratio)
                erp_result = self.change_erp_status(spu_barcode, shop_uid, channel, quantity_type, upload_ratio,storage_uid,virtual_inventory,error_msg)
                erp_result_handle = erp_result[0] if type(erp_result) == tuple else erp_result
                if erp_result_handle is True:
                    print('商品：{0} erp同步库存比例成功'.format(spu_barcode))
                    self.save_erp_switch_es(channel,item,erp_result[1])
                    self.success_save_es(es_data)
                else:
                    error_msg = erp_result[1]
                    print('商品：{0} erp同步库存比例失败'.format(spu_barcode))
                    if not error_msg:
                        error_msg = 'erp同步失败后重试导致的失败'
                    self.error_save_es(es_data,error_msg)
        except Exception:
            print('同步操作失败，失败spu_barcode：{0},channel:{1}'.
                  format(spu_barcode, channel))
            print(traceback.format_exc())
            if not error_msg:
                error_msg = '发生了未被捕捉到的异常错误'
            self.error_save_es(es_data,error_msg)
        finally:
            queue.get()
            queue.task_done()

    @Retry.retry_parameter(5, sleep_time=11)
    def change_erp_status(self, spu_barcode, shop_uid, channel, quantity_type, upload_ratio,storage_uid,virtual_inventory, error_msg,outer_product_id=''):
        ''' 设置万里牛中商品spu的库存比例 '''
        try:
            cookie_num = random.randint(3, 7)
            search_list = InventorySyncConfig(spu_barcode, shop_uid, outer_product_id).set_cookie_position(
                cookie_num).use_cookie_pool().get_result()
            print(search_list)
            if search_list == '会话过期':
                print('erp登陆会话过期。')
                error_msg = 'erp登陆会话过期'
                return False, error_msg
            elif search_list == '查询小红书无outer_product_id':
                print('查询小红书无outer_product_id')
                error_msg = '小红书无outer_product_id，请查询输入参数结构'
                return False, error_msg
            elif not search_list:
                print('{} 在ERP店铺宝贝中找不到该商品。'.format(spu_barcode))
                error_msg = 'ERP店铺宝贝中找不到该商品'
                return 'other', error_msg
            else:
                channel_spucode_list = search_list
                print('channel_spucode_list', channel_spucode_list)
                # 遍历查询到的所有商品，设置例外宝贝库存比例。如果开关状态为0则报错，不设置。
                for _search_item in search_list:
                    if _search_item['upload_status'] == 0:
                        error_msg = 'spu内有开关状态为双关的商品，无法成功设置库存比例'
                        return 'other', error_msg

                for search_item in search_list:
                    upload_status = search_item['upload_status']
                    search_item_id = search_item['item_id']
                    print(search_item_id, upload_status, shop_uid,quantity_type, upload_ratio)
                    InventorySyncUpload(search_item_id, upload_status,shop_uid, quantity_type,
                                        upload_ratio,storage_uid,virtual_inventory)\
                        .set_cookie_position(cookie_num).use_cookie_pool().get_result()
                    time.sleep(0.1)
                print('{0}渠道:{1} erp同步库存比例操作成功'.format(spu_barcode, shop_uid))
                return True, channel_spucode_list
        except Exception:
            print('同步操作失败，失败spu_barcode：{0},channel:{1}'.
                  format(spu_barcode, channel))
            print(traceback.format_exc())
            if not error_msg:
                error_msg = 'ERP同步库存比例异常失败。'
            return False, error_msg

    def erp_shortname_to_shopuid(self, name):
        ''' 获取万里牛中店铺简称对应的shopuid字段 '''
        shopuid_map = {
            '天猫': 'D991C1F60CD5393F8DB19EADE17236F0',
            '奥莱店': 'C91DC23F386A3A97BF61E2A673F20544',
            '小红书': '9A1C9BFF3C67302393D9BE60BB53B8EE',
            '唯品会': 'C9ACE29003EC3B9BB24D01FCFBBF6BE7',
            '京东': '914E617DC96D3442BEC0B5E5844644BF',
            'APP': '7F5259B8A03B37E686C00DD4E33562E5',
        }
        return shopuid_map.get(name, 'other')

    def success_save_es(self, es_data):
        '''操作成功时，更新部分字段后存入es'''
        es_data['syncStatus'] = '同步成功'
        es_data['syncTime'] = str(Date.now().millisecond())
        es_data['failReason'] = ''
        EsInventoryRatioStatus().update([es_data], async=True)
        print('保存成功', es_data)

    def save_erp_switch_es(self, channel, item,channel_spucode_list):
        print('channel_spucode_list', channel_spucode_list)
        try:
            for channel_spucode in channel_spucode_list:
                if VIP_SHOPNAME in channel:
                    fake_sku = channel_spucode['item_id'].split('|')[-1]
                else:
                    fake_sku = channel_spucode['item_id'][2:]
                ratio_data = {
                    'fakeSku': fake_sku,
                    'spuBarcode': item['spuBarcode'],
                    'channel': channel,
                    'name': item.get('name', ''),
                    'channelProductId': item.get('outer_product_id', ''),
                    'storage': item['storage'],
                    'quantityType': item['quantity_type'],
                    'uploadRatio': item['upload_ratio'],
                    'virtualInventory': item['virtual_inventory'],
                    'syncTime': str(Date.now().millisecond()),
                }
                EsInventoryRatio().update([ratio_data], async=True)
                print('保存es成功：', ratio_data)
        except Exception:
            print(traceback.format_exc())
            print('保存es失败：', item)

    def error_save_es(self, es_data,error_msg):
        '''操作失败时，更新部分字段后存入es'''
        es_data['syncStatus'] = '同步失败'
        es_data['syncTime'] = str(Date.now().millisecond())
        if not error_msg:
            error_msg = '未能被捕捉到到异常错误'
        es_data['failReason'] = error_msg
        EsInventoryRatioStatus().update([es_data], async=True)
        self.ding_talk_alarm(es_data, error_msg)
        print('保存成功', es_data)

    @staticmethod
    def ding_talk_alarm(es_data, error_msg):
        token = '87053027d1d9c2ca35b1eda6d248b3d087b764c135f1cb9b1b3387c47322d411'
        title = '万里牛同步库存比例操作报警'
        content = es_data['channel'] + '的商品：' +  es_data['spuBarcode'] + '同步spu库存比例操作失败，原因：' + error_msg
        DingTalk(token, title, content).enqueue()

    def erp_name_change(self,name):
        ''' 获取万里牛中店铺名对应的shopuid字段 '''
        shopuid_map = {
            '[天猫]icy旗舰店': '天猫',
            '[天猫]ICY奥莱': '奥莱店',
            '[小红书]ICY小红书': '小红书',
            '[唯品会JIT]ICY唯品会': '唯品会',
            '[京东]穿衣助手旗舰店': '京东',
            '[穿衣助手]iCY设计师集合店': 'APP',
        }
        return shopuid_map.get(name, 'other')

    def update_inventory_mq(self, barcode_list):
        '''手动更新各渠道库存'''
        from mq_handler import CONST_MESSAGE_TAG_UPDATE_CHANNEL_INVENTORY
        from pyspider.libs.mq import MQ
        MQ().publish_message(CONST_MESSAGE_TAG_UPDATE_CHANNEL_INVENTORY,
                         {"isAll": 0, "spu": barcode_list})

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
                print(Date.now().format(), '==========完成同步所有商品spu例外宝贝库存比例==========')
        else:
            ai_storage_redis.set(status, 1)
            ai_storage_redis.set(progress, 0)
            ai_storage_redis.set(total, 0)
            print(Date.now().format(), '==========完成同步所有商品spu例外宝贝库存比例==========')

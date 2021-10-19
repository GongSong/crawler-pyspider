from gevent import monkey
monkey.patch_all()
import traceback
from hupun_inventory_onsale.page.inventory_sync_upload import InventorySyncUpload
from hupun_inventory_onsale.page.inverntory_sync_config import InventorySyncConfig
from mq_handler.base import Base
from pyspider.helper.date import Date
from pyspider.helper.retry import Retry
import threading
from hupun_slow_crawl.model.es.store_house import StoreHouse
from hupun_inventory_onsale.es.auto_shelf_switch import EsAutoShelfSwitch
from pyspider.helper.es_query_builder import EsQueryBuilder
from hupun_inventory_onsale.on_shelf_config import *
from alarm.page.ding_talk import DingTalk
from hupun_inventory_onsale.es.inventory_ratio import EsInventoryRatio
from hupun_inventory_onsale.es.inventory_ratio_status import EsInventoryRatioStatus
from pyspider.core.model.storage import ai_storage_redis
from pyspider.helper.utils import progress_counter
import time
import queue
import random


class ClearInventoryRatio(Base):
    """
    同步商品的库存比例
    """
    storeuid_dict = StoreHouse().get_all_name_uid_dict()
    max_threads = 6

    def execute(self):
        print('开始清除商品库存的比例')
        self.print_basic_info()
        data = self._data

        total_amount = data.get('total')
        missions_amount = data.get('taskNum')
        mission = 'spu_clear_ratio_mission'
        status = 'spu_clear_ratio_status'
        progress = 'spu_clear_ratio_progress'
        total = 'spu_clear_ratio_total'
        ai_storage_redis.set(total, total_amount)
        # ai_storage_redis.set(mission, 0)
        # ai_storage_redis.set(progress, 0)
        print('总任务数：', missions_amount)

        q = queue.Queue(self.max_threads)

        if data.get('type') == 1:
            print('开始清理所有例外宝贝库存比例')
            # res_list = EsAutoShelfSwitch().scroll(
            #     EsQueryBuilder()
            #         .range('syncTime', Date().now().plus_days(-1)
            #                .format_es_old_utc(), None),
            #     page_size=100
            # )
            # for _list in res_list:
            #     for _item in _list:
            #         channel = self.erp_name_change(_item['channel'])
            #         if channel == '唯品会':
            #             spu_barcode = _item['fakeSku']
            #             data = {"spuBarcode": spu_barcode, "channel": channel}
            #             self.change_upload_ratio_list.append(data)
            #         elif channel == '小红书':
            #             spu_barcode = _item['channelProductId']
            #             try:
            #                 name = _item['name']
            #                 outer_product_id = _item['channelProductId']
            #                 data = {"spuBarcode": spu_barcode, "channel": channel, "name": name,
            #                         "outer_product_id": outer_product_id}
            #                 self.change_upload_ratio_list.append(data)
            #             except:
            #                 print(spu_barcode, '导入失败')
            #         else:
            #             spu_barcode = _item['spuBarcode']
            #             data = {"spuBarcode": spu_barcode, "channel": channel}
            #             self.change_upload_ratio_list.append(data)
            # # 暂不将清除状态（清除中，清除成功，清除失败）写入es。
            # # count = 0
            # # es_list = []
            # # for item in self.change_upload_ratio_list:
            # #     count += 1
            # #     channel = item['channel']
            # #     spu_barcode = item['spuBarcode']
            # #     es_data = {
            # #         "spuBarcode": spu_barcode,
            # #         "channel": channel,
            # #         "syncStatus": '同步中',
            # #         # 对比操作时间，同步最近一天的数据
            # #         "syncTime": str(Date.now().millisecond()),
            # #         "failReason": ""
            # #     }
            # #     es_list.append(es_data)
            # #     if count >= 200:
            # #         EsInventoryRatioStatus().update(es_list, async=True)
            # #         count = 0
            # #         es_list = []
            # # time.sleep(20)
            # thread_list = []
            # for item in self.change_upload_ratio_list:
            #     t = threading.Thread(target=self.consume_task, args=(item,))
            #     thread_list.append(t)
            #     t.start()
            # for thread in thread_list:
            #     thread.join()
            # StorageRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB).delete('shelf.clearSpGoods')
            print('完成清理所有例外宝贝库存比例')

        else:
            print('开始按商品清理例外宝贝库存比例')
            barcode_list = []
            for item in data.get('list'):
                spu_barcode = item['spuBarcode']
                barcode_list.append(spu_barcode)
            for item in data.get('list'):
                q.put(1)
                t = threading.Thread(target=self.consume_task, args=(item, q, ))
                t.start()
            q.join()
            time.sleep(1)

            self.handle_progress_para(missions_amount, mission, status, progress, total)

    @progress_counter('spu_clear_ratio_progress')
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
            shop_uid = self.erp_shortname_to_shopuid(channel)
            storage_uid = item['storage']
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
                erp_result = self.change_erp_status(outer_title, shop_uid, channel,
                                                    storage_uid, error_msg, outer_product_id)
                erp_result_handle = erp_result[0] if type(erp_result) == tuple else erp_result
                if erp_result_handle is True:
                    print('商品：{0} erp同步库存比例成功'.format(outer_title))
                    self.delete_es_by_spu(spu_barcode, channel)
                    self.success_save_es(es_data)
                else:
                    error_msg = erp_result[1]
                    if error_msg == 'ERP店铺宝贝中找不到该商品':
                        self.delete_es_by_spu(spu_barcode, channel)
                        self.error_save_es(es_data, error_msg)
                    else:
                        print('商品：{0} erp同步库存比例失败'.format(outer_title))
                        if not error_msg:
                            error_msg = 'erp同步失败后重试导致的失败'
                        self.error_save_es(es_data, error_msg)
            else:
                print(spu_barcode, shop_uid, channel)
                erp_result = self.change_erp_status(spu_barcode, shop_uid, channel,
                                                    storage_uid, error_msg)
                erp_result_handle = erp_result[0] if type(erp_result) == tuple else erp_result
                if erp_result_handle is True:
                    print('商品：{0} erp同步库存比例成功'.format(spu_barcode))
                    self.delete_es_by_spu(spu_barcode, channel)
                    self.success_save_es(es_data)
                else:
                    error_msg = erp_result[1]
                    if error_msg == 'ERP店铺宝贝中找不到该商品':
                        self.delete_es_by_spu(spu_barcode, channel)
                        self.error_save_es(es_data, error_msg)
                    else:
                        print('商品：{0} erp同步库存比例失败'.format(spu_barcode))
                        if not error_msg:
                            error_msg = 'erp同步失败后重试导致的失败'
                        self.error_save_es(es_data, error_msg)
        except Exception:
            print('同步操作失败，失败spu_barcode：{0},channel:{1}'.
                  format(spu_barcode, channel))
            print(traceback.format_exc())
            if not error_msg:
                error_msg = '发生了未被捕捉到的异常错误'
            self.error_save_es(es_data, error_msg)
        finally:
            queue.get()
            queue.task_done()

    @Retry.retry_parameter(5, sleep_time=11)
    def change_erp_status(self, spu_barcode, shop_uid, channel, storage_uid, error_msg, outer_product_id=''):
        ''' 清除商品spu的库存比例设置 '''
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
                return 'other', error_msg
            elif not search_list:
                print('{} 在ERP店铺宝贝中找不到该商品。'.format(spu_barcode))
                error_msg = 'ERP店铺宝贝中找不到该商品'
                return 'other', error_msg
            else:
                channel_spucode_list = search_list
                print('channel_spucode_list', channel_spucode_list)
                # 遍历查询到的所有商品，如有商品的【自动上架】状态与目标状态不同，则将该商品的状态改为目标状态。
                for search_item in search_list:
                    upload_status = search_item['upload_status']
                    search_item_id = search_item['item_id']
                    print(search_item_id, upload_status, shop_uid)
                    InventorySyncUpload(search_item_id, upload_status,shop_uid, -1, 'null',storage_uid)\
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
        es_data['syncStatus'] = '清理成功'
        es_data['syncTime'] = str(Date.now().millisecond())
        es_data['failReason'] = ''
        EsInventoryRatioStatus().update([es_data], async=True)


    def delete_es_by_channel_productid(self, channel, item, channel_spucode_list):
        '''清除库存比例成功后，删除es库中的该商品记录'''
        print('channel_spucode_list',channel_spucode_list)

        try:
            for channel_spucode in channel_spucode_list:
                if VIP_SHOPNAME in channel:
                    fake_sku = channel_spucode['item_id'].split('|')[-1]
                else:
                    fake_sku = channel_spucode['item_id'][2:]
                try:
                    EsInventoryRatio().delete(fake_sku+'_'+channel+'_'+item['storage'])
                except Exception as e:
                    print('es表中没有该id：{}，删除失败'.format(fake_sku+'_'+channel+'_'+item['storage']))
        except Exception:
            print(traceback.format_exc())

    def error_save_es(self, es_data,error_msg):
        '''操作失败时，更新部分字段后存入es'''
        es_data['syncStatus'] = '清理失败'
        es_data['syncTime'] = str(Date.now().millisecond())
        if not error_msg:
            error_msg = '未能被捕捉到到异常错误'
        es_data['failReason'] = error_msg
        EsInventoryRatioStatus().update([es_data], async=True)
        self.ding_talk_alarm(es_data, error_msg)

    @staticmethod
    def ding_talk_alarm(es_data, error_msg):
        token = '87053027d1d9c2ca35b1eda6d248b3d087b764c135f1cb9b1b3387c47322d411'
        title = '万里牛同步库存比例操作报警'
        content = es_data['channel'] + '的商品：' +  es_data['spuBarcode'] + '清除库存比例操作失败，原因：' + error_msg
        DingTalk(token, title, content).enqueue()

    def erp_name_change(self, name):
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

    def update_inventory_mq_handle(self, barcode_list=[]):
        '''手动更新各渠道库存，传入barcode_list为空时，全量更新'''
        from mq_handler import CONST_MESSAGE_TAG_UPDATE_CHANNEL_INVENTORY
        from pyspider.libs.mq import MQ
        if barcode_list:
            MQ().publish_message(CONST_MESSAGE_TAG_UPDATE_CHANNEL_INVENTORY,
                             {"isAll": 0, "spu": barcode_list})
        else:
            MQ().publish_message(CONST_MESSAGE_TAG_UPDATE_CHANNEL_INVENTORY,
                                 {"isAll": 1, "spu": []})

    def delete_es_by_spu(self,spu_barcode, channel):
        try:
            search_list = EsQueryBuilder().term('spuBarcode', spu_barcode).term('channel', channel).search(EsInventoryRatio(),
                                                                                                1, 100).get_list()
            print(search_list)
            for search_item in search_list:
                try:
                    EsInventoryRatio().delete(search_item['_id'])
                except Exception as e:
                    print('es表中没有该id：{}，删除失败'.format(search_item['_id']))
        except Exception:
            print(traceback.format_exc())

    def handle_progress_para(self, missions_amount, mission, status, progress, total):
        '''进度参数的redis设置'''
        if missions_amount > 1:
            ai_storage_redis.incr(mission)
            time.sleep(1)
            shelf_mission = int(ai_storage_redis.get(mission)) if ai_storage_redis.get(mission) else 0
            print('执行任务数：', shelf_mission)
            if shelf_mission >= missions_amount:
                ai_storage_redis.set(status, 1)
                ai_storage_redis.set(progress, 0)
                ai_storage_redis.set(total, 0)
                ai_storage_redis.set(mission, 0)
                print('=======完成所有商品spu清理例外宝贝库存比例========')
        else:
            ai_storage_redis.set(status, 1)
            ai_storage_redis.set(progress, 0)
            ai_storage_redis.set(total, 0)
            print('=======完成所有商品spu清理例外宝贝库存比例========')

from gevent import monkey
monkey.patch_all()
from mq_handler.base import Base
import traceback
from hupun_inventory_onsale.es.sku_inventory_ratio import EsSkuInventoryRatio
from hupun_inventory_onsale.page.inventory_sync_upload import InventorySyncUpload
from hupun_inventory_onsale.page.search_spu_info import SearchSpuInfo
from hupun_inventory_onsale.page.search_sync_ratio import SearchSyncConfig
from hupun_inventory_onsale.page.vip_sync_ratio import VipSyncRatio
from hupun_slow_crawl.model.es.store_house import StoreHouse
from pyspider.helper.date import Date
from pyspider.helper.retry import Retry
import threading
import random
import queue
from pyspider.helper.es_query_builder import EsQueryBuilder
from pyspider.core.model.storage import ai_storage_redis
from pyspider.helper.utils import generator_list, progress_counter
import time
from alarm.page.ding_talk import DingTalk


class ClearSkuSearchRatio(Base):
    '''清除sku级别库存例外宝贝比例'''
    max_threads = 6

    def execute(self):
        print('开始清除sku的库存例外宝贝')
        self.print_basic_info()
        data = self._data

        total_amount = data.get('total')
        missions_amount = data.get('taskNum')
        mission = 'sku_clear_ratio_mission'
        status = 'sku_clear_ratio_status'
        progress = 'sku_clear_ratio_progress'
        total = 'sku_clear_ratio_total'
        ai_storage_redis.set(total, total_amount)

        try:
            q = queue.Queue(self.max_threads)
            item_list = data.get('list')
            save_list = []
            for item in item_list:
                item_copy = item.copy()

                es_data = {
                    "skuBarcode": item_copy['skuBarcode'],
                    "spuBarcode": item_copy['skuBarcode'][:10],
                    "channel": item_copy['channel'],
                    "syncStatus": '清除中',
                    "syncTime": str(Date.now().millisecond()),
                }
                item_copy.update(es_data)
                save_list.append(item_copy)

            # for _list in generator_list(save_list, 200):
            #     EsSkuInventoryRatio().update(_list)

            for _item in item_list:
                _item_copy = _item.copy()
                q.put(1)
                t = threading.Thread(target=self.consume_task, args=(_item_copy, q,))
                t.start()
            q.join()
        except Exception as e:
            print(traceback.format_exc())
        finally:
            time.sleep(1)
            self.handle_progress_para(missions_amount, mission, status, progress, total)

    @progress_counter('sku_clear_ratio_progress')
    def consume_task(self, _item_copy, queue):
        print('开始消费')
        try:
            result = self.consume(_item_copy)
            result_first_para = result[0] if type(result) == tuple else result
            if result_first_para is True:
                self.delete_es_by_sku(_item_copy['skuBarcode'], _item_copy['channel'])
                print('清除sku成功', _item_copy)
            if result_first_para is not True:
                _item_copy['failReason'] = result[1]
                _item_copy['syncStatus'] = '清除失败'
                _item_copy['syncTime'] = str(Date.now().millisecond())
                print('同步sku失败', _item_copy)
                error_msg = result[1]
                self.ding_talk_alarm(_item_copy, error_msg)
                EsSkuInventoryRatio().update([_item_copy], async=True)
        except Exception as e:
            print(e)
        finally:
            queue.get()
            queue.task_done()

    @Retry.retry_parameter(5, sleep_time=11)
    def consume(self, item):
        try:
            cookie_num = random.randint(3, 7)
            sku_barcode = item['skuBarcode']
            spu_barcode = sku_barcode[:10]
            quantity_type = '-1'
            upload_ratio = '0'
            shop_uid = self.erp_shortname_to_shopuid(item['channel'])
            storage_uid = item['storage']
            # storage_uid = self.storeuid_dict.get(storage)
            virtual_inventory = '0'
            if item['channel'] == '唯品会':
                search_spu_list = SearchSpuInfo(sku_barcode, shop_uid).use_cookie_pool().get_result()
                if search_spu_list == '会话过期':
                    print('erp登陆会话过期。')
                    return False, 'erp登陆会话过期。'
                if search_spu_list == []:
                    print('erp无该spu')
                    return 'other', 'erp无该spu'
                print(search_spu_list)
                for search_item in search_spu_list:
                    VipSyncRatio(search_item['item_id'], search_item['upload_status'], shop_uid, quantity_type, upload_ratio,
                              storage_uid, virtual_inventory).use_cookie_pool().get_result()
                return True

            if item['channel'] == '小红书':
                good_id = 'HS' + item.get('outer_product_id') if item.get('outer_product_id') else item.get('outer_product_id')
                search_spu_list = SearchSyncConfig(good_id, shop_uid, good_id).use_cookie_pool().get_result()
                if search_spu_list == '会话过期':
                    print('erp登陆会话过期。')
                    return False, 'erp登陆会话过期。'
                if search_spu_list == []:
                    print('erp无该spu')
                    return 'other', 'erp无该spu'
                search_list_filter = [_item for _item in search_spu_list if _item['outer_id'] == sku_barcode]
                print(search_list_filter)
                if not search_list_filter:
                    print('erp无该sku')
                    return 'other', 'erp无该sku'
                for search_item in search_list_filter:
                    print(search_item['outer_id'], search_item['item_id'], search_item['upload_status'], shop_uid,
                          quantity_type, upload_ratio,
                          storage_uid, virtual_inventory, search_item['sku_id'])
                    InventorySyncUpload(search_item['item_id'], search_item['upload_status'], shop_uid, quantity_type,
                                        upload_ratio,
                                        storage_uid, virtual_inventory, search_item['sku_id']).use_cookie_pool().get_result()
                return True

            search_spu_list = SearchSpuInfo(spu_barcode, shop_uid).use_cookie_pool().get_result()
            if search_spu_list == '会话过期':
                print('erp登陆会话过期。')
                return False, 'erp登陆会话过期。'
            if search_spu_list == []:
                print('erp无该spu')
                return 'other', 'erp无该spu'

            print('spu列表', search_spu_list)
            for search_spu in search_spu_list:
                search_list = SearchSyncConfig(search_spu['item_id'], shop_uid).use_cookie_pool().get_result()
                if search_list == '会话过期':
                    print('erp登陆会话过期。')
                    return False, 'erp登陆会话过期。'
                if search_list == []:
                    print('该spu中无sku')
                    return 'other', '该spu中无sku'
                else:
                    search_list_filter = [_item for _item in search_list if _item['outer_id'] == sku_barcode]
                    print('sku列表', search_list)
                    if not search_list_filter:
                        print('erp无该sku')
                        return 'other', 'erp无该sku'
                    for search_item in search_list_filter:
                        print(search_item['outer_id'], search_item['item_id'], search_spu['upload_status'], shop_uid, quantity_type, upload_ratio,
                              storage_uid, virtual_inventory, search_item['sku_id'])
                        InventorySyncUpload(search_item['item_id'], search_spu['upload_status'], shop_uid, quantity_type,
                                            upload_ratio,
                                            storage_uid, virtual_inventory, search_item['sku_id'])\
                            .use_cookie_pool().get_result()
            return True
        except Exception as e:
            print(traceback.format_exc())
            print('失败', item)
            return False, '异常失败'

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

    def delete_es_by_sku(self, sku_barcode, channel):
        try:
            search_list = EsQueryBuilder().term('skuBarcode', sku_barcode).term('channel', channel).search(EsSkuInventoryRatio(),
                                                                                                1, 100).get_list()
            print(search_list)
            for search_item in search_list:
                try:
                    EsSkuInventoryRatio().delete(search_item['_id'])
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
            print('总任务数：', shelf_mission)
            if shelf_mission >= missions_amount:
                ai_storage_redis.set(status, 1)
                ai_storage_redis.set(progress, 0)
                ai_storage_redis.set(total, 0)
                ai_storage_redis.set(mission, 0)
                print('==========完成所有商品sku库存例外宝贝的清除==========')
        else:
            ai_storage_redis.set(status, 1)
            ai_storage_redis.set(progress, 0)
            ai_storage_redis.set(total, 0)
            print('==========完成所有商品sku库存例外宝贝的清除==========')

    @staticmethod
    def ding_talk_alarm(es_data, error_msg):
        token = '87053027d1d9c2ca35b1eda6d248b3d087b764c135f1cb9b1b3387c47322d411'
        title = '万里牛清除sku例外宝贝操作报警'
        content = es_data['channel'] + '的商品：' +  es_data['skuBarcode'] + '清除sku例外宝贝库存比例操作失败，原因：' + error_msg
        DingTalk(token, title, content).enqueue()
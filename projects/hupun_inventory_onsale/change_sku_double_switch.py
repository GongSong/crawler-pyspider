from gevent import monkey
monkey.patch_all()
import traceback
from hupun_inventory_onsale.es.es_sku_double_switch import EsSkuDoubleSwitch
from hupun_inventory_onsale.page.sku_double_switch import SkuDoubleSwitch
from hupun_inventory_onsale.page.search_spu_info import SearchSpuInfo
from hupun_inventory_onsale.page.search_sync_ratio import SearchSyncConfig
from pyspider.helper.date import Date
from pyspider.helper.retry import Retry
from pyspider.helper.channel import erp_name_to_shopuid
from hupun_inventory_onsale.page.inventory_sync_upload import InventorySyncUpload
import threading
import random
from mq_handler.base import Base
from hupun_slow_crawl.model.es.store_house import StoreHouse
import queue
from pyspider.core.model.storage import ai_storage_redis
from pyspider.helper.utils import generator_list, progress_counter
import time
from alarm.page.ding_talk import DingTalk


class ChangeSkuDoubleSwitch(Base):
    '''设置sku例外宝贝的【上传库存】和【自动上架】双开关'''
    storeuid_dict = StoreHouse().get_all_name_uid_dict()
    max_threads = 6

    def execute(self):
        print('开始同步sku的双开关状态')
        self.print_basic_info()
        data = self._data

        total_amount = data.get('total')
        missions_amount = data.get('taskNum')
        mission = 'sku_switch_mission'
        status = 'sku_switch_status'
        progress = 'sku_switch_progress'
        total = 'sku_switch_total'
        ai_storage_redis.set(total, total_amount)

        try:
            q = queue.Queue(self.max_threads)
            item_list = data.get('list')
            save_list = []
            for item in item_list:
                item_copy = item.copy()
                for channel in item_copy.get('channels'):
                    es_data = {
                        "skuBarcode": item_copy['skuBarcode'],
                        "spuBarcode": item_copy['skuBarcode'][:10],
                        "channel": channel,
                        "syncStatus": '同步中',
                        "syncTime": str(Date.now().millisecond()),
                    }
                    save_list.append(es_data)

            for _list in generator_list(save_list, 200):
                EsSkuDoubleSwitch().update(_list)

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

    @progress_counter('sku_switch_progress')
    def consume_task(self,_item_copy, queue):
        for channel in _item_copy.get('channels'):
            try:
                self.consume_mini_task(_item_copy, channel)
            except Exception as e:
                print(e)
            finally:
                queue.get()
                queue.task_done()

    def consume_mini_task(self, _item_copy, channel):
        print('开始消费')
        try:
            result = self.consume(_item_copy, channel)
            result_first_para = result[0] if type(result) == tuple else result
            if result_first_para is True:
                save_data = {
                    "skuBarcode": _item_copy['skuBarcode'],
                    "spuBarcode": _item_copy['skuBarcode'][:10],
                    "channel": channel,
                    "inventorySwitchStatus": '开' if _item_copy['inventory_switch'] == 1 else '关',
                    "syncStatus": '同步成功',
                    "syncTime": str(Date.now().millisecond()),
                    "failReason": "",
                }
                if '唯品会' in channel:
                    save_data['switchStatus'] = '开' if _item_copy['inventory_switch'] == 1 else '关'
                print('成功', save_data)
            else:
                save_data = {
                    "skuBarcode": _item_copy['skuBarcode'],
                    "spuBarcode": _item_copy['skuBarcode'][:10],
                    "channel": channel,
                    "syncStatus": '同步失败',
                    "syncTime": str(Date.now().millisecond()),
                    "failReason": result[1],
                }
                print('失败', _item_copy)
                error_msg = result[1]
                self.ding_talk_alarm(_item_copy, error_msg)
            EsSkuDoubleSwitch().update([save_data], async=True)
        except Exception as e:
            print(e)

    @Retry.retry_parameter(5, sleep_time=11)
    def consume(self, item, channel):
        try:
            sku_barcode = item['skuBarcode']
            spu_barcode = sku_barcode[:10]
            shop_uid = erp_name_to_shopuid(channel)
            cookie_num = random.randint(3, 7)
            if '小红书' in channel:
                good_id = 'HS' + item.get('goodsId') if item.get('goodsId') else item.get('goodsId')
                if not good_id:
                    return 'other', '传入有误，无小红书的erp商品id参数'
                search_spu_list = SearchSyncConfig(good_id, shop_uid, good_id).set_cookie_position(
                    cookie_num).use_cookie_pool().get_result()
                print(good_id, shop_uid, good_id)
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
                    print(search_item['outer_id'], search_item['item_id'], item['inventory_switch'], shop_uid,
                          search_item['sku_id'])
                    SkuDoubleSwitch(search_item['item_id'], search_item['sku_id'], item['inventory_switch'],
                                    shop_uid).set_cookie_position(
                        cookie_num).use_cookie_pool().get_result()
                print('成功', item)
                return True

            if '唯品会' in channel:
                search_spu_list = SearchSpuInfo(sku_barcode, shop_uid).set_cookie_position(cookie_num).use_cookie_pool().get_result()
                if search_spu_list == '会话过期':
                    print('erp登陆会话过期。')
                    return False, 'erp登陆会话过期。'
                if search_spu_list == []:
                    print('erp无该spu')
                    return 'other', 'erp无该spu'
                print(search_spu_list)
                for search_item in search_spu_list:
                    print(search_item['item_id'], search_item['sku_id'], item['inventory_switch'],
                                    shop_uid)
                    InventorySyncUpload(search_item['item_id'], 2 * item['inventory_switch'],
                                    shop_uid).set_cookie_position(
                        cookie_num).use_cookie_pool().get_result()
                print('成功', item)
                return True

            search_spu_list = SearchSpuInfo(spu_barcode, shop_uid).set_cookie_position(cookie_num).use_cookie_pool().get_result()
            if search_spu_list == '会话过期':
                print('erp登陆会话过期。')
                return False, 'erp登陆会话过期。'
            if search_spu_list == []:
                print('erp无该spu')
                return 'other', 'erp无该spu'

            for search_spu in search_spu_list:
                search_list = SearchSyncConfig(search_spu['item_id'], shop_uid).set_cookie_position(cookie_num).use_cookie_pool().get_result()
                if search_list == '会话过期':
                    print('erp登陆会话过期。')
                    return False, 'erp登陆会话过期。'
                if search_list == []:
                    print('erp无sku')
                    return 'other', 'erp无sku'
                elif search_list:
                    search_list_filter = [_item for _item in search_list if _item['outer_id'] == sku_barcode]
                    print('sku列表', search_list_filter)
                    if not search_list_filter:
                        print('erp无该sku')
                        return 'other', 'erp无sku'
                    for search_item in search_list_filter:
                        if search_item['outer_id'] == sku_barcode:
                            print(search_item['outer_id'], search_item['item_id'], item['inventory_switch'], shop_uid, search_item['sku_id'])
                            SkuDoubleSwitch(search_item['item_id'], search_item['sku_id'], item['inventory_switch'], shop_uid).set_cookie_position(
                                cookie_num).use_cookie_pool().get_result()
            return True
        except Exception as e:
            print(traceback.format_exc())
            # print('失败', item)
            return False, '异常失败'

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
                print('==========完成所有商品sku例外宝贝双开关的设置==========')
        else:
            ai_storage_redis.set(status, 1)
            ai_storage_redis.set(progress, 0)
            ai_storage_redis.set(total, 0)
            print('==========完成所有商品sku例外宝贝双开关的设置==========')

    @staticmethod
    def ding_talk_alarm(es_data, error_msg):
        token = '87053027d1d9c2ca35b1eda6d248b3d087b764c135f1cb9b1b3387c47322d411'
        title = '万里牛例外宝贝sku双开关操作报警'
        content = es_data['channel'] + '的商品：' +  es_data['skuBarcode'] + '操作sku双开关失败，原因：' + error_msg
        DingTalk(token, title, content).enqueue()

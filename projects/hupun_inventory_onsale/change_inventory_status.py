import gevent.monkey
gevent.monkey.patch_ssl()
from hupun_inventory_onsale.es.auto_shelf_switch import EsAutoShelfSwitch
from hupun_inventory_onsale.page.weipinhui_operate_shelf_status import VipOperateShelfStatus
from hupun_inventory_onsale.es.vip_product_detail import EsVipProductDetail
from pyspider.helper.es_query_builder import EsQueryBuilder
import traceback
from hupun_inventory_onsale.es.shelf_status import EsShelfObtainedStatus
from hupun_inventory_onsale.page.inventory_sync_upload import InventorySyncUpload
from hupun_inventory_onsale.page.inverntory_sync_config import InventorySyncConfig
from pyspider.helper.channel import erp_name_to_shopuid, erp_name_to_tm_storekey
from pyspider.helper.date import Date
from pyspider.helper.retry import Retry
from mq_handler.base import Base
import time
import requests
import json
from hupun_inventory_onsale.on_shelf_config import *
from alarm.page.ding_talk import DingTalk
import threading
from pyspider.helper.utils import generator_list, progress_counter
import queue
from pyspider.core.model.storage import ai_storage_redis
import random


class ChangeInventoryStatus(Base):
    '''
    操作erp库存商品【自动上架】设置的开启和关闭
    '''
    max_threads = 4

    def execute(self):
        print('开始进行商品的上下架操作')
        self.print_basic_info()
        data = self._data

        total_amount = data.get('total')
        missions_amount = data.get('taskNum')
        mission = 'shelf_mission'
        status = 'shelf_status'
        progress = 'shelf_progress'
        total = 'shelf_total'
        ai_storage_redis.set(total, total_amount)

        try:
            q = queue.Queue(self.max_threads)
            save_list = []
            for items in data.get('goodsId'):
                spu_barcode = items.get('spuBarcode')
                for channel in items.get('channel'):
                    es_data = {
                        "spuBarcode": spu_barcode,
                        "channel": channel,
                        "syncStatus": '同步中',
                        # 对比操作时间，同步最近一天的数据
                        "syncTime": str(Date.now().millisecond()),
                    }
                    save_list.append(es_data)

            for _list in generator_list(save_list, 200):
                EsShelfObtainedStatus().update(_list)

            # 此处变更，将引起渠道后台上下架码变更。如需修改，请检查渠道上下架代码是否需同步变更
            target_status = 2 * (1 - data.get('upload'))
            user_id = data.get('sessionId')
            for _items in data.get('goodsId'):
                spu_barcode = _items.get('spuBarcode')
                for channel in _items.get('channel'):
                    q.put(1)
                    t = threading.Thread(target=self.consume_task, args=(target_status, spu_barcode, channel, _items, user_id, q, ))
                    t.start()
            q.join()
            time.sleep(1)

            self.handle_progress_para(missions_amount, mission, status, progress, total)

        except Exception as e:
            print(traceback.format_exc())

    @progress_counter('shelf_progress')
    def consume_task(self, target_status, spu_barcode, channel, items, user_id, queue):
        # 传入的upload=0上架，1下架。万里牛的target_status=0下架按钮双关，2上架按钮双开。
        print('开始消费：', spu_barcode, channel, target_status)
        es_data = {
            "spuBarcode": spu_barcode,
            "channel": channel,
        }
        error_msg = ''
        try:
            shop_uid = erp_name_to_shopuid(channel)
            if shop_uid == 'other':
                error_msg = 'erp查询渠道出现错误，请确认传入商品渠道信息'
                # 需处理异常
                raise Exception('查询渠道{0} 出现错误，请确认传入商品渠道信息'.format(channel))

            # 小红书
            elif REDBOOK_SHOPNAME in channel:
                outer_title = items.get('name')
                if not outer_title:
                    error_msg = '小红书商品未传入中文名，无法查询'
                    raise Exception('小红书商品无中文名，请确认传入参数')
                outer_title = outer_title.strip()
                outer_product_id = 'HS' + items.get('productId')
                # 小红书渠道用小红书的商品名作为搜索输入，且必须有小红书的barcode，即outer_product_id
                erp_result = self.change_erp_status(outer_title, shop_uid, target_status, error_msg, outer_product_id)
                erp_result_handle = erp_result[0] if type(erp_result) == tuple else erp_result
                if erp_result_handle is True:
                    print('商品：{0} erp同步操作成功'.format(outer_title))
                    hs_channel_result = self.sync_rb_shelf_status(outer_product_id, target_status)
                    hs_channel_result_handle = hs_channel_result[0] if type(hs_channel_result) == tuple else hs_channel_result
                    if hs_channel_result_handle:
                        print('商品:{} 完整同步上下架成功'.format(outer_title))
                        self.success_save_es(es_data, target_status)
                        self.save_erp_switch_es(items, channel, target_status, erp_result[1])
                    else:
                        print('商品：{0} 渠道后台同步上下架失败'.format(outer_title))
                        self.error_save_es(es_data, hs_channel_result[1])
                        # 如果失败，则将万里牛中开关改为原来状态
                        init_target_status = erp_result[1][0]['upload_status']
                        self.fail_revert_erp_switch(items, channel, outer_title, shop_uid,
                                                    init_target_status, error_msg, outer_product_id)
                else:
                    print('商品：{0} erp同步操作失败'.format(outer_title))
                    error_msg = erp_result[1]
                    if not error_msg:
                        error_msg = 'erp同步失败后重试导致的失败'
                    self.error_save_es(es_data, error_msg)

            # 天猫
            elif TMALL_SHOPNAME in channel:
                erp_result = self.change_erp_status(spu_barcode, shop_uid, target_status, error_msg)
                erp_result_handle = erp_result[0] if type(erp_result) == tuple else erp_result
                if erp_result_handle is True:
                    print('商品：{0} erp同步操作成功'.format(spu_barcode))
                    tm_channel_result = self.sync_tm_shelf_status(channel, target_status, erp_result[1])
                    tm_channel_result_handle = tm_channel_result[0] if type(tm_channel_result) == tuple else tm_channel_result
                    if tm_channel_result_handle:
                        print('商品:{} 完整同步上下架成功'.format(spu_barcode))
                        self.success_save_es(es_data, target_status)
                        self.save_erp_switch_es(items, channel, target_status, erp_result[1])
                    else:
                        print('商品：{0} 渠道后台同步上下架失败'.format(spu_barcode))
                        self.error_save_es(es_data, tm_channel_result[1])
                        init_target_status = erp_result[1][0]['upload_status']
                        self.fail_revert_erp_switch(items, channel, spu_barcode, shop_uid, init_target_status, error_msg)
                else:
                    print('商品：{0} erp同步操作失败'.format(spu_barcode))
                    error_msg = erp_result[1]
                    if not error_msg:
                        error_msg = 'erp同步失败后重试导致的失败'
                    self.error_save_es(es_data, error_msg)

            # 京东
            elif JD_SHOPNAME in channel:
                erp_result = self.change_erp_status(spu_barcode, shop_uid, target_status, error_msg)
                erp_result_handle = erp_result[0] if type(erp_result) == tuple else erp_result
                if erp_result_handle is True:
                    print('商品：{0} erp同步操作成功'.format(spu_barcode))
                    jd_channel_result = self.sync_jd_shelf_status(target_status, erp_result[1])
                    jd_channel_result_handle = jd_channel_result[0] if type(jd_channel_result) == tuple else jd_channel_result
                    if jd_channel_result_handle:
                        print('商品:{} 完整同步上下架成功'.format(spu_barcode))
                        self.success_save_es(es_data, target_status)
                        self.save_erp_switch_es(items, channel, target_status, erp_result[1])
                    else:
                        print('商品：{0} 渠道后台同步上下架失败'.format(spu_barcode))
                        self.error_save_es(es_data, jd_channel_result[1])
                        init_target_status = erp_result[1][0]['upload_status']
                        self.fail_revert_erp_switch(items, channel, spu_barcode, shop_uid, init_target_status, error_msg)
                else:
                    print('商品：{0} erp同步操作失败'.format(spu_barcode))
                    error_msg = erp_result[1]
                    if not error_msg:
                        error_msg = 'erp同步失败后重试导致的失败'
                    self.error_save_es(es_data, error_msg)

            # APP
            elif ICY_SHOPNAME in channel:
                app_goods_id = items.get('appGoodsId', '')
                erp_result = self.change_erp_status(spu_barcode, shop_uid, target_status, error_msg)
                erp_result_handle = erp_result[0] if type(erp_result) == tuple else erp_result
                if erp_result_handle is True:
                    print('商品：{0} erp同步操作成功'.format(spu_barcode))
                    icy_channel_result = self.sync_icy_shelf_status(app_goods_id, target_status, user_id)
                    icy_channel_result_handle = icy_channel_result[0] if type(icy_channel_result) == tuple else icy_channel_result
                    if icy_channel_result_handle is True:
                        print('商品:{} 完整同步上下架成功'.format(spu_barcode))
                        self.success_save_es(es_data, target_status)
                        self.save_erp_switch_es(items, channel, target_status, erp_result[1])
                    else:
                        print('商品：{0} 渠道后台同步上下架失败'.format(spu_barcode))
                        self.error_save_es(es_data, icy_channel_result[1])
                        init_target_status = erp_result[1][0]['upload_status']
                        self.fail_revert_erp_switch(items, channel, spu_barcode, shop_uid, init_target_status, error_msg)
                else:
                    print('商品：{0} erp同步操作失败'.format(spu_barcode))
                    error_msg = erp_result[1]
                    if not error_msg:
                        error_msg = 'erp同步失败后重试导致的失败'
                    self.error_save_es(es_data, error_msg)

            # 唯品会
            elif VIP_SHOPNAME in channel:
                time.sleep(0.1)
                erp_result = self.change_erp_status(spu_barcode, shop_uid, target_status, error_msg)
                erp_result_handle = erp_result[0] if type(erp_result) == tuple else erp_result
                if erp_result_handle is True:
                    print('商品：{0} erp同步操作成功'.format(spu_barcode))
                    vip_channel_result = self.sync_vip_shelf_status(spu_barcode, target_status)
                    vip_channel_result_handle = vip_channel_result[0] if type(vip_channel_result) == tuple else vip_channel_result
                    if vip_channel_result_handle:
                        print('商品:{} 完整同步上下架成功'.format(spu_barcode))
                        self.success_save_es(es_data, target_status)
                        self.save_erp_switch_es(items, channel, target_status, erp_result[1])
                    else:
                        print('商品：{0} 渠道后台同步上下架失败'.format(spu_barcode))
                        self.error_save_es(es_data, vip_channel_result[1])
                        init_target_status = erp_result[1][0]['upload_status']
                        self.fail_revert_erp_switch(items, channel, spu_barcode, shop_uid, init_target_status, error_msg)
                else:
                    print('商品：{0} erp同步操作失败'.format(spu_barcode))
                    error_msg = erp_result[1]
                    if not error_msg:
                        error_msg = 'erp同步失败后重试导致的失败'
                    self.error_save_es(es_data, error_msg)

            else:
                print('未知店铺渠道，请确定传入参数')
                print(traceback.format_exc())
                error_msg = '未知店铺渠道，请确定传入参数'
                self.error_save_es(es_data, error_msg)

        except Exception:
            print('同步操作失败，失败spu_barcode：{0},channel:{1},target_status:{2}'.
                  format(spu_barcode, channel, target_status))
            print(traceback.format_exc())
            if not error_msg:
                error_msg = '发生了未被捕捉到的异常错误'
            self.error_save_es(es_data, error_msg)

        finally:
            queue.get()
            queue.task_done()

    @Retry.retry_parameter(5, sleep_time=11)
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
                # 遍历查询到的所有商品，如有商品的【自动上架】状态与目标状态不同，则将该商品的状态改为目标状态。
                for search_item in search_list:
                    upload_status = search_item['upload_status']
                    search_item_id = search_item['item_id']
                    if upload_status != target_status:
                        InventorySyncUpload(search_item_id, target_status).set_cookie_position(cookie_num).use_cookie_pool().get_result()
                        time.sleep(0.1)
                # 修改状态完成后，再次查询检测。如仍有与目标状态不同的商品，则返回错误，进行重试。
                checked_list = InventorySyncConfig(spu_barcode, shop_uid, outer_product_id).set_cookie_position(
                    cookie_num).use_cookie_pool().get_result()
                for check_item in checked_list:
                    _upload_status = check_item['upload_status']
                    if _upload_status != target_status:
                        print('操作未完全成功')
                        error_msg = 'ERP库存同步修改失败。'
                        return False, error_msg
                print('{0}渠道:{1} erp同步上下架状态操作成功'.format(spu_barcode, shop_uid))
                return True, search_list
        except Exception:
            print('同步操作失败，失败spu_barcode：{0},channel:{1},target_status:{2}'.
                  format(spu_barcode, shop_uid, target_status))
            print(traceback.format_exc())
            if not error_msg:
                error_msg = 'ERP库存同步修改失败。'
            return False, error_msg

    @Retry.retry_parameter(2, sleep_time=5)
    def sync_rb_shelf_status(self, spu_barcode, target_status):
        ''' 更改小红书后台商品上下架设置 '''
        try:
            # target_status等于2时上架，其他为下架
            available = True if target_status == 2 else False
            data = {
                'spuId': spu_barcode[2:],
                'available': available,
            }
            channel_result_json = requests.post(RB_SHELF_URL, data=json.dumps(data),
                                                headers={'Content-Type': 'application/json'}, timeout=30).json()
            print(channel_result_json)
            res = channel_result_json['success']
            if not len(channel_result_json['data']):
                error_msg = '渠道后台找不到该商品'
                return 'other', error_msg
            if not res:
                error_msg = '渠道后台同步上下架失败'
                return False, error_msg
            else:
                return True
        except Exception:
            error_msg = '渠道后台同步上下架失败'
            print(traceback.format_exc())
            return False, error_msg

    @Retry.retry_parameter(2, sleep_time=5)
    def sync_tm_shelf_status(self, channel, target_status, channel_spucode_list):
        try:
            if target_status == 2:
                # target_status等于2时商品上架，其余为下架
                url = TM_ON_SHELF_URL
                print(channel_spucode_list)
                post_data = {
                    "num": 0,
                    "num_iid": int(channel_spucode_list[0]['item_id'][2:]),
                    "storeKey": erp_name_to_tm_storekey(channel)
                }
                channel_result_json = requests.post(url, data=json.dumps(post_data),
                                                    headers={'Content-Type': 'application/json'},
                                                    timeout=30).json()
                res = channel_result_json.get('item_update_listing_response', '')
                print(channel_result_json)

            else:
                url = TM_OFF_SHELF_URL
                print(channel_spucode_list)
                post_data = {
                    "num_iid": int(channel_spucode_list[0]['item_id'][2:]),
                    "storeKey": erp_name_to_tm_storekey(channel)
                }
                channel_result_json = requests.post(url, data=json.dumps(post_data),
                                                    headers={'Content-Type': 'application/json'},
                                                    timeout=30).json()
                res = channel_result_json.get('item_update_delisting_response', '')
                print(channel_result_json)
            not_find_item = channel_result_json.get('error_response', {}).get('sub_msg', '')
            if not_find_item == 'ITEM_NOT_FOUND':
                error_msg = '渠道后台找不到该商品'
                return 'other', error_msg
            if TM_OFF_SHELF_ERROR in not_find_item:
                error_msg = '当前时间段该商品不允许下架'
                return 'other', error_msg
            if not res:
                error_msg = '渠道后台同步上下架失败'
                return False, error_msg
            else:
                return True

        except Exception:
            print('渠道后台同步上下架执行报错')
            error_msg = '渠道后台同步上下架失败'
            print(traceback.format_exc())
            return False, error_msg

    @Retry.retry_parameter(2, sleep_time=5)
    def sync_jd_shelf_status(self, target_status, channel_spucode_list):
        try:
            url = JD_SHELF_URL
            # target_status中0为下架，2为上架。jd的op_type中1为上架，2为下架。
            op_type = 2 - 0.5 * target_status
            post_data = {
                "wareId": int(channel_spucode_list[0]['item_id'][2:]),
                "opType": op_type
            }
            channel_result_json = requests.post(url, data=json.dumps(post_data),
                                                headers={'Content-Type': 'application/json'}, timeout=30).json()
            res = channel_result_json.get('success', '')
            not_find_item = channel_result_json.get('zhDesc', '获取失败')
            if not_find_item:
                if '商品不属于该商家' in not_find_item:
                    error_msg = '渠道后台找不到该商品'
                    return 'other', error_msg
            if not res:
                print(channel_spucode_list, target_status, channel_result_json)
                error_msg = '渠道后台同步上下架失败'
                return False, error_msg
            else:
                return True
        except Exception:
            print('渠道后台同步上下架执行报错')
            error_msg = '渠道后台同步上下架失败'
            print(traceback.format_exc())
            return False, error_msg

    @Retry.retry_parameter(2, sleep_time=5)
    def sync_icy_shelf_status(self, app_goods_id, target_status, user_id):
        try:
            url = ICY_SHELF_RUL
            # 上下架状态，target为0时下架，2时上架；is_soldout为0上架，1下架
            is_sold_out = 1 - 0.5 * target_status
            if not app_goods_id:
                print('传入数据中该商品的app渠道的id为空')
                error_msg = '传入数据中该商品的app渠道的id为空'
                return False, error_msg
            app_shelf_list = [app_goods_id]
            params = {"goodsIds": app_shelf_list, "isSoldOut": is_sold_out}
            post_data = {'data': json.dumps(params), 'sessionUserId': user_id}
            channel_result_json = requests.post(url, data=json.dumps(post_data),
                                                headers={'Content-Type': 'application/json'}, timeout=30).json()
            channel_result = json.dumps(channel_result_json, ensure_ascii=False)
            if '商品不存在' in channel_result:
                print('渠道后台找不到该商品')
                error_msg = '渠道后台找不到该商品'
                return 'other', error_msg
            if '库存不足' in channel_result:
                print('app库存不足')
                error_msg = 'app库存不足'
                return 'other', error_msg
            success_response = channel_result_json.get('data', {}).get('success', '')
            err_msg_response = channel_result_json.get('data', {}).get('errMsg', '无数据')
            if success_response == 1 and not err_msg_response:
                print('app渠道后台上下架操作成功')
                return True
            else:
                print('渠道后台同步上下架失败')
                error_msg = '渠道后台同步上下架失败'
                return False, error_msg
        except Exception:
            print('渠道后台同步上下架执行报错')
            error_msg = '渠道后台同步上下架失败'
            print(traceback.format_exc())
            return False, error_msg

    @Retry.retry_parameter(2, sleep_time=5)
    def sync_vip_shelf_status(self, spu_barcode, target_status):
        try:
            # 上下架状态，target为0时下架，2时上架; 0下架，1上架
            state = 0.5 * target_status
            post_data = []
            items = EsQueryBuilder().term('osn.keyword', spu_barcode).search(EsVipProductDetail(), 1,
                                                                             100).get_list()
            for item in items:
                param = {"merchandiseNo": item.get('merchandiseNo', '')}
                post_data.append(param)
            channel_result = VipOperateShelfStatus(post_data, state).get_result()
            success_code = '"code":"200"'
            success_msg = '"success":true'
            if '会话过期' in channel_result:
                error_msg = '唯品会后台登陆会话过期'
                return False, error_msg
            if '商品信息不存在' in channel_result:
                error_msg = '渠道后台找不到该商品'
                return 'other', error_msg
            if success_code in channel_result and success_msg in channel_result:
                print('app渠道后台上下架操作成功')
                return True
            else:
                error_msg = '渠道后台同步上下架失败'
                return False, error_msg
        except Exception:
            print('渠道后台同步上下架执行报错')
            error_msg = '渠道后台同步上下架失败'
            print(traceback.format_exc())
            return False, error_msg

    def error_save_es(self, es_data, error_msg):
        '''操作失败时，更新部分字段后存入es'''
        es_data['syncStatus'] = '同步失败'
        es_data['syncTime'] = str(Date.now().millisecond())
        if not error_msg:
            error_msg = '未能被捕捉到到异常错误'
        es_data['failReason'] = error_msg
        EsShelfObtainedStatus().update([es_data], async=True)
        self.ding_talk_alarm(es_data, error_msg)
        print('保存操作错误成功', es_data)

    def success_save_es(self, es_data, target_status):
        '''操作成功时，更新部分字段后存入es'''
        es_data['syncStatus'] = '同步成功'
        es_data['syncTime'] = str(Date.now().millisecond())
        es_data['shelfStatus'] = '上架' if target_status == 2 else '下架'
        es_data['failReason'] = ''
        EsShelfObtainedStatus().update([es_data], async=True)
        print('保存成功', es_data)

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

    @staticmethod
    def ding_talk_alarm(es_data, error_msg):
        token = '87053027d1d9c2ca35b1eda6d248b3d087b764c135f1cb9b1b3387c47322d411'
        title = '渠道同步上下架商品报警'
        content = es_data['channel'] + '的商品：' + es_data['spuBarcode'] + '同步上下架操作失败，原因：' + error_msg
        DingTalk(token, title, content).enqueue()

    def fail_revert_erp_switch(self, items, channel, spu_barcode, shop_uid, init_target_status, error_msg, outer_product_id=''):
        fail_erp_result = self.change_erp_status(spu_barcode, shop_uid, init_target_status, error_msg, outer_product_id)
        fail_erp_result_handle = fail_erp_result[0] if type(fail_erp_result) == tuple else fail_erp_result
        if fail_erp_result_handle is True:
            self.save_erp_switch_es(items, channel, init_target_status, fail_erp_result[1])

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
                print(Date.now().format(), '==========完成商品的上下架操作==========')
        else:
            ai_storage_redis.set(status, 1)
            ai_storage_redis.set(progress, 0)
            ai_storage_redis.set(total, 0)
            print(Date.now().format(), '==========完成商品的上下架操作==========')

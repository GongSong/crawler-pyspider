import gevent.monkey
gevent.monkey.patch_ssl()
import fire
import time
import json
from hupun_inventory_onsale.es.vip_product_detail import EsVipProductDetail
from hupun_inventory_onsale.page.inventory_query_switch_status import InventoryQuerySwitchStatus
from hupun_inventory_onsale.page.weipinhui_query_shelf_status import VipQueryShelfStatus
from hupun_inventory_onsale.page.weipinhui_query_stock import VipQueryStock
from pyspider.helper.es_query_builder import EsQueryBuilder
from pyspider.helper.date import Date
import random
from alarm.page.ding_talk import DingTalk
import traceback
from hupun_inventory_onsale.es.es_sku_double_switch import EsSkuDoubleSwitch
from hupun_inventory_onsale.page.search_sync_ratio import SearchSyncConfig
from hupun_inventory_onsale.page.weipinhui_query_sku_stock import VipQuerySkuStock


class Cron:
    def vip_query_shelf_status(self):
        print(Date.now(), '开始爬取唯品会商品上下架信息')
        total_page = 0
        init_page = 3
        current_page = 1
        while current_page <= max(total_page, init_page):
            res = VipQueryShelfStatus(current_page).get_result()
            print(current_page)
            current_page += 1
            time.sleep(random.randrange(5, 10))
            print(res)
            if total_page == 0:
                try:
                    search_total_page = json.loads(res).get('total') // 100 + 1
                    print(search_total_page)
                except:
                    search_total_page = 0
                if search_total_page != 0:
                    total_page = search_total_page

    def vip_query_stock(self):
        print(Date.now(), '开始爬取唯品会商品库存信息')
        search_list = EsVipProductDetail().scroll(
            EsQueryBuilder()
                .source(['merchandiseNo', 'sellChannel']),
            page_size=100
        )
        for _list in search_list:
            item_list = []
            for _item in _list:
                item_list.append(_item)
            # print(item_list)
            VipQueryStock(item_list).get_result()
            time.sleep(random.randrange(5, 10))

    def vip_query_sku_stock(self):
        print(Date.now(), '开始爬取唯品会商品sku库存信息')
        search_list = EsVipProductDetail().scroll(
            EsQueryBuilder()
                .source(['merchandiseNo', 'sellChannel']),
            page_size=100
        )
        for _list in search_list:
            item_list = []
            for _item in _list:
                item_list.append(_item)
                VipQuerySkuStock(_item).get_result()
            time.sleep(random.randrange(1, 5))

    def vip_manage_query(self):
        try:
            self.vip_query_shelf_status()
            time.sleep(10)
            self.vip_query_stock()
            time.sleep(10)
            self.vip_query_sku_stock()
            print('唯品会轮询库存成功')
        except:
            print(traceback.format_exc())
            token = '87053027d1d9c2ca35b1eda6d248b3d087b764c135f1cb9b1b3387c47322d411'
            title = '唯品会轮询爬虫报警'
            content = '唯品会轮询失败，请查看登陆是否过期'
            print(Date.now(), content)
            # DingTalk(token, title, content).enqueue()


    def query_one_channel_switch_status(self, channel):
        print(Date.now(), '开始爬取{}商品上下架开关信息'.format(channel))
        total_page = 0
        init_page = 3
        current_page = 1
        while current_page <= max(total_page, init_page):
            res = InventoryQuerySwitchStatus(channel, current_page).set_cookie_position(2).use_cookie_pool().get_result()
            print(current_page)
            current_page += 1
            time.sleep(1)
            # print(res)
            if total_page == 0:
                try:
                    search_total_page = res['data'].get('pageCount')
                    print(search_total_page)
                except:
                    search_total_page = 0
                if search_total_page != 0:
                    total_page = search_total_page

    def query_switch_status(self):
        channel_list = [
                        '[天猫]icy旗舰店',
                        '[天猫]ICY奥莱',
                        '[小红书]ICY小红书',
                        '[唯品会JIT]ICY唯品会',
                        '[京东]穿衣助手旗舰店',
                        '[穿衣助手]iCY设计师集合店'
                        ]
        for channel in channel_list:
            self.query_one_channel_switch_status(channel)

    def check_vip_cookie(self):
        print(Date.now(), '开始检查唯品会cookie是否失效')
        try:
            VipQueryShelfStatus(1, only_check=True).get_result()
        except Exception as e:
            print(traceback.format_exc())
            token = '87053027d1d9c2ca35b1eda6d248b3d087b764c135f1cb9b1b3387c47322d411'
            title = '唯品会cookie失效爬虫报警'
            content = '唯品会cookie检测失败，请查看登陆是否过期'
            print(Date.now(), content)
            DingTalk(token, title, content).enqueue()

    def query_one_channel_sku_switch(self, channel):
        print(Date.now(), '开始爬取{}商品上下架开关信息'.format(channel))
        total_page = 0
        init_page = 3
        current_page = 1
        while current_page <= max(total_page, init_page):
            try:
                position_no = random.randint(3, 7)
                res = InventoryQuerySwitchStatus(channel, current_page, is_save=False).set_cookie_position(
                    position_no).use_cookie_pool().get_result()
                time.sleep(1)
                item_list = res['data']['data']
                es_list = []
                for _item in item_list:
                    try:
                        position_no = random.randint(3, 7)
                        if '小红书' in channel:
                            sku_res = SearchSyncConfig(_item.get('itemID'), _item.get('shopID'),
                                                       _item.get('itemID')).set_cookie_position(position_no)\
                                .use_cookie_pool().get_result()
                        else:
                            sku_res = SearchSyncConfig(_item.get('itemID'), _item.get('shopID'),
                                                       '').set_cookie_position(position_no)\
                                .use_cookie_pool().get_result()
                        for i in sku_res:
                            es_data = {
                                'skuBarcode': i['outer_id'],
                                'spuBarcode': i['outer_id'][:10],
                                'channel': channel,
                                'inventorySwitchStatus': '关' if i['upload_status'] == 0 else '开',
                                'syncTime': str(Date.now().millisecond())
                            }
                            es_list.append(es_data)
                            print('es_data', es_data)
                    except:
                        print(traceback.format_exc())
                print('保存')
                EsSkuDoubleSwitch().update(es_list, async=True)
            except:
                print(traceback.format_exc())
            finally:
                current_page += 1

            if total_page == 0:
                try:
                    search_total_page = res['data'].get('pageCount')
                except:
                    search_total_page = 0
                if search_total_page != 0:
                    total_page = search_total_page

    def query_sku_switch(self):
        channel_list = [
                        '[天猫]icy旗舰店',
                        '[天猫]ICY奥莱',
                        '[小红书]ICY小红书',
                        '[京东]穿衣助手旗舰店',
                        '[穿衣助手]iCY设计师集合店'
                        ]
        for channel in channel_list:
            self.query_one_channel_sku_switch(channel)
        # 万里牛的唯品会本身即为sku级别，故直接调用。唯品会的开关状态同时写入两个es表中。
        self.query_one_channel_switch_status('[唯品会JIT]ICY唯品会')


if __name__ == '__main__':
    fire.Fire(Cron)

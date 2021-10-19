import fire
import time
import json

from hupun_inventory_onsale.es.es_sku_double_switch import EsSkuDoubleSwitch
from hupun_inventory_onsale.es.vip_product_detail import EsVipProductDetail
from hupun_inventory_onsale.page.inventory_query_switch_status import InventoryQuerySwitchStatus
from hupun_inventory_onsale.page.search_sync_ratio import SearchSyncConfig
from hupun_inventory_onsale.page.weipinhui_query_shelf_status import VipQueryShelfStatus
from hupun_inventory_onsale.page.weipinhui_query_stock import VipQueryStock
from pyspider.helper.es_query_builder import EsQueryBuilder
from pyspider.helper.date import Date
import random
from alarm.page.ding_talk import DingTalk
import traceback


channel = '[小红书]ICY小红书'


def query_one_channel_sku_switch(channel):
    print(Date.now(), '开始爬取{}商品上下架开关信息'.format(channel))
    total_page = 0
    init_page = 3
    current_page = 1
    while current_page <= max(total_page, init_page):
        try:
            position_no = random.randint(3, 7)
            res = InventoryQuerySwitchStatus(channel, current_page, is_save=False).set_cookie_position(position_no).get_result(retry_limit=3, retry_interval=60)
            time.sleep(1)
            item_list = res['data']['data']
            es_list = []
            for _item in item_list:
                try:
                    position_no = random.randint(3, 7)
                    if '小红书' in channel:
                        sku_res = SearchSyncConfig(_item.get('itemID'), _item.get('shopID'), _item.get('itemID')).set_cookie_position(position_no).get_result(retry_limit=3, retry_interval=60)
                    else:
                        sku_res = SearchSyncConfig(_item.get('itemID'), _item.get('shopID'), '').set_cookie_position(position_no).get_result(retry_limit=3, retry_interval=60)
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

query_one_channel_sku_switch(channel)

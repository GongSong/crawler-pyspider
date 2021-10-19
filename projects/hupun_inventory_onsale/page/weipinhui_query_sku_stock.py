from hupun_inventory_onsale.es.vip_sku_stock import EsVipSkuStock
from pyspider.helper.es_query_builder import EsQueryBuilder
from hupun_inventory_onsale.es.vip_product_detail import EsVipProductDetail
import json
from alarm.page.ding_talk import DingTalk
from hupun_inventory_onsale.page.weipinhui_operate_shelf_status import get_jsession_cookie
from pyspider.libs.base_crawl import *
from weipinhui_migrate.config import *
from hupun.page.base import *
from hupun_inventory_onsale.on_shelf_config import *


class VipQuerySkuStock(BaseCrawl):
    def __init__(self, data):
        """
        唯品会 查询 商品sku库存
        """
        super(VipQuerySkuStock, self).__init__()
        self.data = data
        self.jsession = "JSESSIONID=" + get_jsession_cookie()
        self.url = VIP_SKU_STOCK_URL

    def crawl_builder(self):
        return CrawlBuilder() \
            .set_url(self.url) \
            .set_cookies(self.jsession) \
            .set_headers_kv('User-Agent', USER_AGENT) \
            .set_post_json_data(self.data)

    def parse_response(self, response, task):
        sync_time = Date.now().format_es_utc_with_tz()
        print(response.text)
        res_json = json.loads(response.text).get('data', [])
        if len(res_json):
            res_list = []
            for _key in res_json:
                _res = {}
                _res['syncTime'] = sync_time
                _res['skuBarcode'] = _key.get('barcode')
                _res['spuBarcode'] = _key.get('barcode', [])[:10]
                _res['skuStock'] = _key.get('bindMerItemLeavingNum')
                res_list.append(_res)
            EsVipSkuStock().update(res_list, async=True)
        return response.text

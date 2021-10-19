import gevent.monkey
gevent.monkey.patch_ssl()
from pyspider.helper.es_query_builder import EsQueryBuilder
from hupun_inventory_onsale.es.vip_product_detail import EsVipProductDetail
import json
from alarm.page.ding_talk import DingTalk
from hupun_inventory_onsale.page.weipinhui_operate_shelf_status import get_jsession_cookie
from pyspider.libs.base_crawl import *
from weipinhui_migrate.config import *
from hupun.page.base import *
from hupun_inventory_onsale.on_shelf_config import *


class VipQueryStock(BaseCrawl):
    def __init__(self, data):
        """
        唯品会 档期详情数据 分天查看的表格下载
        """
        super(VipQueryStock, self).__init__()
        self.data = data
        self.jsession = "JSESSIONID=" + get_jsession_cookie()
        self.url = VIP_STOCK_URL

    def crawl_builder(self):
        return CrawlBuilder() \
            .set_url(self.url) \
            .set_cookies(self.jsession) \
            .set_headers_kv('User-Agent', USER_AGENT) \
            .set_post_json_data(self.data)

    def parse_response(self, response, task):
        sync_time = Date.now().format_es_utc_with_tz()
        res_json = json.loads(response.text).get('data', [])
        if len(res_json.keys()):
            res_list = []
            for _key in res_json.keys():
                _res = {}
                _res['sync_time'] = sync_time
                _res['merchandiseNo'] = res_json.get(_key).get('merchandiseNo')
                _res['bindLeavingNum'] = res_json.get(_key).get('bindMerLeavingNum')
                res_list.append(_res)
            EsVipProductDetail().update(res_list, async=True)
        return response.text


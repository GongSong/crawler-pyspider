import gevent.monkey
gevent.monkey.patch_ssl()
from hupun_inventory_onsale.es.vip_product_detail import EsVipProductDetail
import json
from alarm.page.ding_talk import DingTalk
from hupun_inventory_onsale.page.weipinhui_operate_shelf_status import get_jsession_cookie
from pyspider.libs.base_crawl import *
from weipinhui_migrate.config import *
from hupun.page.base import *
from hupun_inventory_onsale.on_shelf_config import *



class VipQueryShelfStatus(BaseCrawl):
    def __init__(self, page_no, param={}, only_check=False):
        """
        唯品会 查询商品上下架状态和商品对应的唯品会id
        """
        super(VipQueryShelfStatus, self).__init__()
        self.data = {"pageNo": page_no, "pageSize": 100, "param": param}
        self.jsession = "JSESSIONID=" + get_jsession_cookie()
        self.url = VIP_SHELF_STATUS_URL
        self.only_check = only_check

    def crawl_builder(self):
        return CrawlBuilder() \
            .set_url(self.url) \
            .set_cookies(self.jsession) \
            .set_headers_kv('User-Agent', USER_AGENT)\
            .set_post_json_data(self.data)

    def parse_response(self, response, task):
        sync_time = Date.now().format_es_utc_with_tz()
        res_json = json.loads(response.text).get('data', [])
        if self.only_check is True:
            if len(res_json) == 0:
                print('检查cookie失败')
                raise Exception('未爬取到信息')
            else:
                print('检查cookie成功')
            return
        if len(res_json):
            for _item in res_json:
                _item['sync_time'] = sync_time
                # 删除库存字段，避免空库存字段覆盖掉真实库存
                del _item['bindMerLeavingNum']
            EsVipProductDetail().update(res_json, async=True)
        return response.text


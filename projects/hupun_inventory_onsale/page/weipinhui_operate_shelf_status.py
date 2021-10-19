import gevent.monkey
gevent.monkey.patch_ssl()
from alarm.page.ding_talk import DingTalk
from pyspider.libs.base_crawl import *
from weipinhui_migrate.config import *
import requests
from hupun_inventory_onsale.on_shelf_config import *
import re


def get_jsession_cookie():
    ctime = round(time.time())
    save_url = default_storage_redis.get('vip_product_url')
    token_url = re.search('\?(.*?)$', save_url)
    url = 'https://nov-admin.vip.com/vendor/normal/normalMerchandise?' + token_url[1] \
        if token_url else JSESSIONID_URL.format(ctime)
    session = requests.Session()
    session.get(url, headers=JSESSIONID_HEADERS)
    cookies = requests.utils.dict_from_cookiejar(session.cookies)
    return cookies.get('JSESSIONID', '')


class VipOperateShelfStatus(BaseCrawl):
    def __init__(self, post_data, state):
        """
        唯品会 操作商品上下架
        """
        super(VipOperateShelfStatus, self).__init__()
        self.data = post_data
        # state为0下架，1上架
        self.url = VIP_SHELF_URL.format(state)
        self.jsession = "JSESSIONID=" + get_jsession_cookie()
        print(self.jsession)

    def crawl_builder(self):
        return CrawlBuilder() \
            .set_url(self.url) \
            .set_cookies(self.jsession) \
            .set_headers_kv('User-Agent', USER_AGENT)\
            .set_post_json_data(self.data)

    def parse_response(self, response, task):
        print(response.text)
        return response.text

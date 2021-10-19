from cookie.config import *
from cookie.model.data import Data
from cookie.page.hupun_login_entry import HupunLoginEntry
from pyspider.libs.base_crawl import *


class HupunLoginAccount(BaseCrawl):
    """
    hupun 的 cookie 获取的入口地址的第 1 个链接
    """

    URL = Data.CONST_HUPUN_LOGIN_DOMIN + 'login'

    def __init__(self, username, password, cookies=None):
        super(HupunLoginAccount, self).__init__()
        self.__cookies = cookies
        self.__username = username
        self.__password = password

    def crawl_builder(self):
        builder = CrawlBuilder() \
            .set_url(self.URL + "#{}".format(self.__username)) \
            .set_headers_kv('User-Agent', USER_AGENT)
        if self.__cookies:
            builder.set_cookies_dict(self.__cookies)
        return builder

    def parse_response(self, response, task):
        status_code = response.status_code
        redirect_url = response.url
        seted_cookie = response.cookies
        self.crawl_handler_page(HupunLoginEntry(self.__username, self.__password, seted_cookie))
        return {
            'status_code': status_code,
            'redirect_url': redirect_url,
            'seted_cookie': seted_cookie,
        }

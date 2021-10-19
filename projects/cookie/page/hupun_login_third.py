from cookie.config import *
from cookie.model.data import Data
from cookie.page.hupun_login_cookie_init import HupunLoginCookieInit
from pyspider.libs.base_crawl import *


class HupunLoginThird(BaseCrawl):
    """
    hupun 的 cookie 获取的入口地址的第 3 个链接
    新 - 20200809
    """

    URL = Data.CONST_HUPUN_LOGIN_DOMIN + 'service/authentication/update/login/company'

    def __init__(self, username, cookies=None):
        super(HupunLoginThird, self).__init__()
        self.__cookies = cookies
        self.__username = username

    def crawl_builder(self):
        builder = CrawlBuilder() \
            .set_url(self.URL + "#{}".format(self.__username)) \
            .set_headers_kv('User-Agent', USER_AGENT)\
            .set_post_data_kv('companyID', 'D1E338D6015630E3AFF2440F3CBBAFAD')\
            .set_post_data_kv('application', '2')\
            .set_post_data_kv('hot', 'true')\
            .set_post_data_kv('fastChoose', 'true')\

        if self.__cookies:
            self.__cookies['account'] = self.__username
            builder.set_cookies_dict(self.__cookies)
        return builder

    def parse_response(self, response, task):
        status_code = response.status_code
        redirect_url = response.url
        seted_cookie = response.cookies
        self.crawl_handler_page(HupunLoginCookieInit(self.__username, seted_cookie))
        return {
            'status_code': status_code,
            'redirect_url': redirect_url,
            'seted_cookie': seted_cookie,
        }

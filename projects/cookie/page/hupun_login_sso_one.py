from cookie.config import *
from cookie.page.hupun_login_sso_two import HupunLoginSsoTwo
from pyspider.libs.base_crawl import *


class HupunLoginSsoOne(BaseCrawl):
    """
    hupun 的 cookie 获取的入口地址的第 3 个链接
    已失效 - 20200809
    """

    URL = 'https://account.hupun.com/service/sso/cookie/init?token={}&key=account.hupun.com'

    def __init__(self, username, cookies=None):
        super(HupunLoginSsoOne, self).__init__()
        self.__cookies = cookies
        self.__username = username

    def crawl_builder(self):
        token = self.__cookies['CALFSESSIONID']
        builder = CrawlBuilder() \
            .set_url(self.URL.format(token) + "#{}".format(self.__username)) \
            .set_headers_kv('User-Agent', USER_AGENT)
        if self.__cookies:
            builder.set_cookies_dict(self.__cookies)
        return builder

    def parse_response(self, response, task):
        status_code = response.status_code
        redirect_url = response.url
        seted_cookie = response.cookies
        self.crawl_handler_page(HupunLoginSsoTwo(self.__username, seted_cookie))
        return {
            'status_code': status_code,
            'redirect_url': redirect_url,
            'seted_cookie': seted_cookie,
        }

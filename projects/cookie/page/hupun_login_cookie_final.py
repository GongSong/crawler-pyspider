from alarm.page.ding_talk import DingTalk
from cookie.config import *
from pyspider.libs.base_crawl import *
from cookie.model.data import Data as CookieData


class HupunLoginCookieFinal(BaseCrawl):
    """
    hupun 的 cookie 获取的入口地址的最后获取链接,在这个页面拿到可用cookie
    已失效 - 20200809
    """

    URL = 'https://erp.hupun.com/homePage.d?_calf=erp-web'

    def __init__(self, username, cookies):
        super(HupunLoginCookieFinal, self).__init__()
        self.__cookies = cookies
        self.__username = username

    def crawl_builder(self):
        builder = CrawlBuilder() \
            .set_url(self.URL + "#{}".format(self.__username)) \
            .set_headers_kv('User-Agent', USER_AGENT) \
            .set_cookies_dict(self.__cookies)
        return builder

    def parse_response(self, response, task):
        status_code = response.status_code
        redirect_url = response.url
        seted_cookie = response.cookies

        if 'expired' in redirect_url:
            # 发送报警
            title = 'hupun 账号登录失败，请检查登录接口'
            text = 'hupun 账号{}登录失败，请检查登录接口'.format(self.__username)
            self.crawl_handler_page(DingTalk(ROBOT_TOKEN, title, text))
            return {
                'msg': 'hupun登录失败，请检查登录接口',
                'status_code': status_code,
                'redirect_url': redirect_url,
                'seted_cookie': seted_cookie,
                'response': response.content
            }

        cookies_str = "; ".join([str(x) + "=" + str(y) for x, y in seted_cookie.items()])
        CookieData.set(CookieData.CONST_PLATFORM_HUPUN, self.__username, cookies_str)

        return {
            'status_code': status_code,
            'redirect_url': redirect_url,
            'seted_cookie': seted_cookie,
        }

from alarm.page.ding_talk import DingTalk
from backstage_data_migrate.config import ROBOT_TOKEN
from cookie.model.data import Data
from cookie.page.hupun_login_third import HupunLoginThird
from pyspider.libs.base_crawl import *


class HupunLoginEntry(BaseCrawl):
    """
    hupun 的 cookie 获取的入口地址的第 2 个链接
    """

    URL = Data.CONST_HUPUN_LOGIN_DOMIN + 'service/login'

    def __init__(self, username, password, cookies):
        super(HupunLoginEntry, self).__init__()
        self.__cookies = cookies
        self.__username = username
        self.__password = password

    def crawl_builder(self):
        account = self.__username
        password = self.__password
        builder = CrawlBuilder() \
            .set_url(self.URL + "#{}".format(self.__username)) \
            .set_post_data_kv('account', account) \
            .set_post_data_kv('password', password) \
            .set_post_data_kv('mode', 'Password')

        if self.__cookies:
            builder.set_cookies_dict(self.__cookies)
        return builder

    def parse_response(self, response, task):
        try:
            # response.json 用来检测是否抓到了数据
            text = response.json
            status_code = response.status_code
            redirect_url = response.url
            seted_cookie = response.cookies
            self.crawl_handler_page(HupunLoginThird(self.__username, seted_cookie))
            return {
                'status_code': status_code,
                'redirect_url': redirect_url,
                'seted_cookie': seted_cookie,
            }

        except Exception as e:
            processor_logger.exception('hupun login error: {}'.format(e))
            title = '万里牛账号登录失败报警'
            text = '万里牛账号登录失败：{}'.format(e)
            self.crawl_handler_page(DingTalk(ROBOT_TOKEN, title, text))

        return {
            'url': response.url,
            'msg': '已获取cookie',
            'content': response.text,
            'seted_cookie': response.cookies,
        }

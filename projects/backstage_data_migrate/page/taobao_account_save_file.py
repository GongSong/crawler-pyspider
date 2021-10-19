from pyspider.libs.oss import oss
from pyspider.libs.utils import md5string

from alarm.page.ding_talk import DingTalk
from backstage_data_migrate.config import *
from pyspider.helper.logging import processor_logger
from pyspider.libs.base_crawl import BaseCrawl
from pyspider.libs.crawl_builder import CrawlBuilder
from cookie.model.data import Data as CookieData


class AccountSave(BaseCrawl):
    """
    淘宝后台订单账号数据保存
    """

    def __init__(self, username, apply_time, url):
        super(AccountSave, self).__init__()
        self.__username = username
        self.__url = url
        self.__apply_time = apply_time

    def crawl_builder(self):
        builder = CrawlBuilder() \
            .set_url(self.__url) \
            .set_cookies(CookieData.get(CookieData.CONST_PLATFORM_TAOBAO_MYSELLER, self.__username)) \
            .set_headers_kv('User-Agent', USER_AGENT) \
            .schedule_age() \
            .set_task_id(md5string(self.__username + self.__url))
        return builder

    def parse_response(self, response, task):
        # 判断是否获取到了内容
        if '订单编号' in response.text and '买家支付宝账号' in response.text:
            # 保存数据到oss
            file_path = oss.get_key(
                oss.CONST_TAOBAO_ACCOUNT_PATH,
                '{apply_date}.csv'.format(apply_date=self.__apply_time)
            )
            oss.upload_data(file_path, response.content)
            return {
                'msg': '已保存数据到oss',
                'url': self.__url,
                'apply_time': self.__apply_time,
            }
        else:
            processor_logger.warning('没有拿到数据内容, 请检查 cookie 是否有效')
            token = '8d67692c0106afe9379b44df67f9a0b4ecfc24a0fcdcfba4381bc334b550cdfc'
            title = '淘宝后台订单账号数据 cookie 获取异常报警'
            content = '淘宝后台订单账号数据没有拿到正确的 cookie, 请检查 cookie 更新的脚本'
            self.crawl_handler_page(DingTalk(token, title, content))

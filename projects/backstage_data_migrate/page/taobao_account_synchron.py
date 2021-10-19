from bs4 import BeautifulSoup

from backstage_data_migrate.page.taobao_account_save_file import AccountSave
from pyspider.libs.oss import oss
from pyspider.libs.utils import md5string

from alarm.page.ding_talk import DingTalk
from backstage_data_migrate.config import *
from pyspider.helper.logging import processor_logger
from pyspider.libs.base_crawl import BaseCrawl
from pyspider.libs.crawl_builder import CrawlBuilder
from cookie.model.data import Data as CookieData


class TaobaoAccount(BaseCrawl):
    """
    淘宝后台订单账号数据下载
    """
    TAOBAO_URL = 'https://trade.taobao.com/trade/itemlist/list_export_order.htm?page_no=1'

    def __init__(self, username):
        super(TaobaoAccount, self).__init__()
        self.__username = username

    def crawl_builder(self):
        builder = CrawlBuilder() \
            .set_url(self.TAOBAO_URL) \
            .set_cookies(CookieData.get(CookieData.CONST_PLATFORM_TAOBAO_MYSELLER, self.__username)) \
            .set_headers_kv('User-Agent', USER_AGENT) \
            .schedule_age() \
            .set_task_id(md5string(self.__username + self.TAOBAO_URL))
        return builder

    def parse_response(self, response, task):
        try:
            soup = BeautifulSoup(response.text)
            tag_li = soup.find_all('li')
            for li in tag_li:
                apply_time = li.find('h2', class_='sheet-item-hd').get_text().split('报表申请时间：', 1)[1].strip()
                apply_time = apply_time.replace(' ', '_')
                excel_url = li.find('a', class_='long-btn').attrs['href']

                # 判断是否已经有文件，有则跳过
                file_path = oss.get_key(
                    oss.CONST_TAOBAO_ACCOUNT_PATH,
                    '{apply_date}.csv'.format(apply_date=apply_time)
                )
                if oss.is_had(file_path):
                    processor_logger.info('已存在路径 {}，跳过抓取'.format(apply_time))
                else:
                    self.crawl_handler_page(AccountSave(self.__username, apply_time, excel_url))

        except Exception as e:
            processor_logger.error(e)
            processor_logger.warning('没有拿到正确的 cookie, 请检查 cookie 更新的脚本')
            token = '8d67692c0106afe9379b44df67f9a0b4ecfc24a0fcdcfba4381bc334b550cdfc'
            title = '淘宝后台订单账号数据 cookie 获取失败报警'
            content = '淘宝后台订单账号数据没有拿到正确的 cookie, 请检查 cookie 更新的脚本'
            self.crawl_handler_page(DingTalk(token, title, content))

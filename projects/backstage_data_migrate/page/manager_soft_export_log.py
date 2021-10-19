import uuid

from bs4 import BeautifulSoup
from backstage_data_migrate.config import *
from backstage_data_migrate.page.manager_soft_download_file import ManagerSoftDownFile
from pyspider.helper.date import Date
from pyspider.helper.logging import processor_logger
from pyspider.libs.base_crawl import BaseCrawl
from pyspider.libs.crawl_builder import CrawlBuilder
from cookie.model.data import Data as CookieData


class ManagerSoftExLog(BaseCrawl):
    """
    发送导出掌柜软件的商品的请求
    """
    EXPORT_URL = 'http://tb.maijsoft.cn/index.php?r=export/getLogList&dt=html&_={}'

    def __init__(self, username, compare_date, compare_words, channel):
        """
        导出商品的请求
        :param username: 掌柜软件的cookie
        :param compare_date: 用于参照导出商品的日期
        :param compare_words: 用于参照导出商品的类型
        :param channel: 保存数据的渠道（店铺）
        """
        super(ManagerSoftExLog, self).__init__()
        self.__username = username
        self.__compare_date = compare_date
        self.__compare_words = compare_words
        self.__channel = channel

    def crawl_builder(self):
        cookie = CookieData.get(CookieData.CONST_PLATFORM_TAOBAO_MANAGER_SOFT, self.__username)
        builder = CrawlBuilder() \
            .set_url(self.EXPORT_URL.format(Date.now().millisecond())) \
            .set_cookies(cookie) \
            .set_headers_kv('User-Agent', USER_AGENT) \
            .set_task_id(uuid.uuid4())
        return builder

    def parse_response(self, response, task):
        result = BeautifulSoup(response.text, 'lxml')
        trs = result.find_all('tr')
        for _tr in trs:
            tds = _tr.find_all('td')
            tr_time = tds[1].get_text()
            time_to_date = Date(tr_time)
            export_category = tds[2].get_text().strip().split(' ', 1)[0]
            download_url = tds[4].find_all('a')[1]['href']
            if export_category == self.__compare_words and time_to_date > Date(self.__compare_date):
                processor_logger.info('time: {}'.format(tr_time))
                processor_logger.info('export_category: {}'.format(export_category))
                processor_logger.info('download_url: {}'.format(download_url))
                ManagerSoftDownFile(download_url, self.__compare_words, self.__channel).enqueue()
                return True
        return False

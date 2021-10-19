import uuid

from pyspider.helper.excel_reader import ExcelReader
from pyspider.libs.base_crawl import *
from alarm.page.ding_talk import DingTalk
from urllib import parse
from pyspider.helper.excel import Excel
from cookie.model.data import Data as CookieData


class CommonGet(BaseCrawl):
    """
    通用的GET请求
    """

    def __init__(self, url, return_type='word_text'):
        super(BaseCrawl, self).__init__()
        self.url = url
        self.return_type = return_type

    def crawl_builder(self):
        return CrawlBuilder() \
            .set_url(self.url) \
            .set_task_id(uuid.uuid4()) \
            .set_cookies(CookieData.get(CookieData.CONST_PLATFORM_HUPUN, CookieData.CONST_USER_HUPUN[0][0]))

    def parse_response(self, response, task):
        if self.return_type == 'word_text':
            result = response.doc.text()
        else:
            result = response.text
        return result

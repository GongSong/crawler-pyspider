import uuid
import json

from pyspider.libs.base_crawl import *
from pyspider.helper.logging import processor_logger
from backstage_data_migrate.config import *
from cookie.model.data import Data as CookieData
from pyspider.libs.utils import md5string


class RedbookVisitorMsg(BaseCrawl):
    """
    小红书后台数据获取---访客数
    """
    URL = 'https://ark.xiaohongshu.com/api/ark/chaos/trd/realtime/trend?type=1&current_date={}&compared_date={}#{}'
    random_id = uuid.uuid4()
    website = 'redbook'

    def __init__(self, date, username, retry=RETRY_TIMES):
        super(RedbookVisitorMsg, self).__init__()
        self.__date = date
        self.__url = self.URL.format(self.__date, self.__date, self.random_id)
        self.__retry = retry
        self.__username = username

    def crawl_builder(self):
        cookies_dict_trans = {}
        cookies_dict = [i.strip().split('=', 1) for i in
                        CookieData.get(CookieData.CONST_PLATFORM_REDBOOK, self.__username).split(';')]
        for cookie in cookies_dict:
            cookies_dict_trans[cookie[0]] = cookie[1]
        return CrawlBuilder()\
            .set_url(self.__url)\
            .set_cookies_dict(cookies_dict_trans)\
            .set_headers_kv('User-Agent', USER_AGENT)\
            .set_task_id(md5string(self.__username+self.__url))\
            .schedule_age(1)

    def parse_response(self, response, task):
        content = response.text
        js_content = json.loads(content)
        code = js_content['success']
        processor_logger.info('获取的code：{}'.format(code))
        if code is not True:
            if self.__retry > 0:
                processor_logger.warning('没有拿到json内容，再次重试，重试次数：{}'.format(self.__retry))
                self.__retry -= 1
                self.crawl_handler_page(RedbookVisitorMsg(self.__date, self.__username, self.__retry))
            else:
                processor_logger.warning('已达到重试次数，退出')
                return {
                    'error_msg': 'reach retry times:{}, stop crawl'.format(RETRY_TIMES),
                    'contentSize': len(response.content),
                    'result': content
                }
        else:
            processor_logger.info('拿到了json内容')
            return {
                'url': self.__url,
                'result': content,
                'create_time': self.__date,
                'website': self.website,
                'data': json.dumps(js_content),
                'data_type': '访客数'
            }

import uuid
import json

from pyspider.libs.base_crawl import *
from backstage_data_migrate.config import *
from cookie.model.data import Data as CookieData
from pyspider.libs.utils import md5string


class JDViewFlow(BaseCrawl):
    """
    获取京东流量概况信息
    """
    URL = 'https://sz.jd.com/sz/api/viewflow/getCoreIndexData.ajax?cmpType=0&date={date}&endDate={end_date}' \
          '&startDate={start_date}#{id}'

    website = 'jingdong'
    random_id = uuid.uuid4()

    def __init__(self, date, end_date, start_date, date_type_name, username, retry=RETRY_TIMES):
        super(JDViewFlow, self).__init__()
        self.__date = date
        self.__end_date = end_date
        self.__start_date = start_date
        self.__retry = retry
        self.__date_type_name = date_type_name
        self.__username = username
        self.__url = self.URL.format(date=self.__date, end_date=self.__end_date, start_date=self.__start_date,
                                     id=self.random_id)

    def crawl_builder(self):
        cookies = CookieData.get(CookieData.CONST_PLATFORM_JINGDONG, CookieData.CONST_USER_JINGDONG[0][0])
        if not cookies:
            processor_logger.warning('there is no cookies, pls check the cookies pool.')
            return {
                'error project': "backstage-jingdong",
                'error_msg': "there is no cookies, pls check the cookies pool.",
                'username': self.__username,
            }
        return CrawlBuilder() \
            .set_url(self.__url) \
            .set_cookies(cookies) \
            .set_headers_kv('User-Agent', USER_AGENT) \
            .set_task_id(md5string(self.__date_type_name + self.__url)) \
            .schedule_age(1)

    def parse_response(self, response, task):
        content = response.text
        summary_json = json.loads(content)
        summary_code = summary_json['status']
        processor_logger.info('数据看板获取的code：{}'.format(summary_code))
        if int(summary_code) != 0:
            processor_logger.warning('没拿到json内容，重试次数还剩：{}次'.format(self.__retry))
            if self.__retry < 1:
                processor_logger.warning('重试次数达到{}次，退出{}'.format(self.__retry, self.__date_type_name))
                return {
                    'url': self.__url,
                    'error_msg': 'reach retry times:{}, stop crawl.'.format(RETRY_TIMES),
                    'contentSize': len(response.content),
                    'result': content
                }
            else:
                self.__retry -= 1
                self.crawl_handler_page(
                    JDViewFlow(self.__date, self.__end_date, self.__start_date, self.__date_type_name, self.__username,
                               self.__retry))
        else:
            processor_logger.info('拿到了{}的json内容'.format(self.__date_type_name))

            # 更新流量看板数据
            return {
                'url': self.__url,
                'result': content,
                'create_time': self.__start_date,
                'website': self.website,
                'data': json.dumps(summary_json),
                'data_type': self.__date_type_name
            }

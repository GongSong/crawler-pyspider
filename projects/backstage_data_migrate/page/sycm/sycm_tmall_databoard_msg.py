import json

from pyspider.libs.base_crawl import *
from pyspider.helper.date import Date
from pyspider.helper.logging import processor_logger
from backstage_data_migrate.config import *
from cookie.model.data import Data as CookieData
from pyspider.libs.utils import md5string


class SycmTmallDataBoardMsg(BaseCrawl):
    """
    获取生意参谋淘宝天猫后台的表格数据--流量看板信息
    实时数据
    """
    URL = 'https://sycm.taobao.com/flow/new/live/guide/trend/overview.json?device=0'
    website = 'sycm'

    def __init__(self, username, channel, retry=RETRY_TIMES):
        super(SycmTmallDataBoardMsg, self).__init__()
        self.__url = self.URL
        self.__username = username
        self.__channel = channel
        self.__create_time = Date.now().to_hour_start().format()
        self.__retry = retry

    def crawl_builder(self):
        return CrawlBuilder() \
            .set_url(self.__url) \
            .set_cookies(CookieData.get(CookieData.CONST_PLATFORM_TAOBAO_SYCM, self.__username)) \
            .set_headers_kv('User-Agent', USER_AGENT) \
            .set_task_id(md5string(self.__username + self.__url + self.__create_time))

    def parse_response(self, response, task):
        content = response.text

        js_content = json.loads(content)
        code = js_content['code']
        processor_logger.info('获取的code：{}'.format(code))
        if int(code) != 0:
            if self.__retry > 0:
                processor_logger.warning('没拿到json内容，再次重试，重试次数'.format(self.__retry))
                self.__retry -= 1
                self.crawl_handler_page(SycmTmallDataBoardMsg(self.__username, self.__channel, self.__retry))
            else:
                processor_logger.warning('已达到重试次数，退出')
                return {
                    'url': self.__url,
                    'error_msg': 'reach retry times: {}, stop crawl.'.format(RETRY_TIMES),
                    'contentSize': len(response.content),
                    'result': content
                }
        else:
            processor_logger.info('拿到了流量看板的json内容')
            hour = Date.now().to_hour_start().timestamp()
            channel = self.website + ':' + self.__channel
            # 更新流量看板数据
            return {
                'url': self.__url,
                'result': content,
                'create_time': self.__create_time,
                'website': channel,
                'data': json.dumps(js_content),
                'data_type': "流量看板",
                'hour': hour
            }

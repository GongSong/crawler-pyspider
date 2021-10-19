import uuid
import json

from backstage_data_migrate.config import *
from pyspider.libs.base_crawl import *
from pyspider.helper.date import Date
from alarm.page.ding_talk import DingTalk
from cookie.model.data import Data as CookieData
from pyspider.libs.utils import md5string


class SycmYesterdayTmallTaobaoData(BaseCrawl):
    """
    获取生意参谋历史的天猫淘宝后台数据-流量看板
    更新: 添加了一个天猫店铺，取消了淘宝店铺的抓取
    """
    URL = 'https://sycm.taobao.com/flow/new/guide/trend/overview.json?device=0&dateType={0}&dateRange={1}%7C{2}#{3}'
    website = 'sycm'
    random_id = uuid.uuid4()

    def __init__(self, date_type, start_time, end_time, date_type_name,
                 username, channel, delay_second=None):
        super(SycmYesterdayTmallTaobaoData, self).__init__()
        self.__date_type = date_type
        self.__start_time = start_time
        self.__end_time = end_time
        self.__date_type_name = date_type_name
        self.__delay_second = delay_second
        self.__username = username
        self.__channel = channel
        self.__url = self.URL.format(self.__date_type, self.__start_time,
                                     self.__end_time, self.random_id)

    def crawl_builder(self):
        builder = CrawlBuilder() \
            .set_url(self.__url) \
            .set_cookies(CookieData.get(CookieData.CONST_PLATFORM_TAOBAO_SYCM, self.__username)) \
            .set_headers_kv('User-Agent', USER_AGENT) \
            .set_task_id(md5string(self.__username + self.__url)) \
            .schedule_age(1)
        if self.__delay_second:
            builder.schedule_delay_second(self.__delay_second)
        return builder

    def parse_response(self, response, task):
        content = response.text

        js_content = json.loads(content)
        code = js_content['code']
        processor_logger.info('获取的code：{}'.format(code))
        if int(code) != 0:
            processor_logger.warning('未获取到生意参谋历史后台数据')
            if int(Date.now().strftime('%H')) > 16:
                processor_logger.warning(
                    '生意参谋历史后台数据抓取失败，请检查Mac-Pro上的cookie获取模块')
                title = '生意参谋历史后台数据获取爬虫报警'
                text = '生意参谋历史{}-{}-{}后台数据获取失败,请检查Mac-Pro的cookie获取模块'.format(
                    self.__date_type_name, self.__start_time, self.__end_time)
                self.crawl_handler_page(DingTalk(ROBOT_TOKEN, title, text))
                return {
                    'error_msg': text,
                    'content': content
                }
            self.crawl_handler_page(
                SycmYesterdayTmallTaobaoData(self.__date_type,
                                             self.__start_time,
                                             self.__end_time,
                                             self.__date_type_name,
                                             self.__username,
                                             self.__channel,
                                             delay_second=3600))
        else:
            processor_logger.info('拿到了流量看板的json内容')
            channel = self.website + ':' + self.__channel

            # 更新流量看板数据
            return {
                'url': self.__url,
                'result': content,
                'create_time': self.__start_time,
                'website': channel,
                'data': json.dumps(js_content),
                'data_type': self.__date_type_name
            }

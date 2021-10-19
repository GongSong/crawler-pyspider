from pyspider.libs.base_crawl import *
from pyspider.helper.date import Date
from cookie.model.data import Data as CookieData
from taobao_tables_download.config import *
from pyspider.libs.utils import md5string
from taobao_tables_download.save_to_oss import save_to_oss
from alarm.page.ding_talk import DingTalk


class ShopAllDay(BaseCrawl):
    URL = 'https://sycm.taobao.com/adm/v2/downloadBySchema.do?name={}&' \
          'logicType=shop&dimId=1&themeId=1,2,3,4,5,6,7,8,9,10&startDate={}' \
          '&endDate={}&isAutoUpdate=Y&deviceType=1,0,2' \
          '&indexCode=1,2,5,116,117,118,132,133,134,142,143,144,153,154,155,' \
          '162,163,164,171,172,173,180,181,182,189,190,191,198,199,200,207,' \
          '208,209,216,217,218,225,226,227,234,235,236,243,244,245,252,253,' \
          '254,261,262,263,270,271,272,279,280,281,288,289,290,297,298,299,' \
          '306,307,308,309,310,311,324,325,326,333,334,335,342,371,372,378,' \
          '383,403,404,405,407,408,409,410,412,413,414,415,519,570,571,572,' \
          '588,589,590,597,598,599,606,607,608&dateType=day&reportType=1'

    def __init__(self, file_name, start_date, end_date, username, channel, delay_second=None):
        super(ShopAllDay, self).__init__()
        self.__file_name = file_name
        self.__start_date = start_date
        self.__end_date = end_date
        self.__username = username
        self.__channel = channel
        self.__delay_second = delay_second
        self.__url = self.URL.replace(',', '%2C').format(self.__file_name,
                                                         self.__start_date,
                                                         self.__end_date)

    def crawl_builder(self):
        builder = CrawlBuilder() \
            .set_url(self.__url) \
            .set_cookies(CookieData.get(CookieData.CONST_PLATFORM_TAOBAO_SYCM,
                                        self.__username)) \
            .set_headers_kv('User-Agent', USER_AGENT) \
            .set_task_id(md5string(
            self.__file_name + self.__start_date + self.__end_date + self.__username))
        if self.__delay_second:
            builder.schedule_delay_second(self.__delay_second)
        return builder

    def parse_response(self, response, task):
        is_success = save_to_oss(self.__file_name, response, self.__channel)
        split_name_list = self.__file_name.split('T', 1)
        if is_success is False:
            processor_logger.warning('未获取到{}数据'.format(split_name_list[0]))
            if int(Date.now().strftime('%H')) > UNTIL_HOUR:
                title = '{}抓取失败'.format(split_name_list[0])
                text = '{}渠道的{}抓取失败，请检查Mac-Pro的cookie获取模块' \
                    .format(self.__channel, split_name_list[0])
                self.crawl_handler_page(DingTalk(ROBOT_TOKEN, title, text))
                return {
                    'error_msg': text,
                    'content': response.content
                }
            self.crawl_handler_page(ShopAllDay(self.__file_name,
                                               self.__start_date,
                                               self.__end_date,
                                               self.__username,
                                               self.__channel,
                                               delay_second=DELAY_SECOND))
        else:
            processor_logger.info('拿到了{}的数据'.format(split_name_list[0]))

from pyspider.libs.base_crawl import *
from pyspider.helper.date import Date
from cookie.model.data import Data as CookieData
from taobao_tables_download.config import *
from pyspider.libs.utils import md5string
from taobao_tables_download.save_to_oss import save_to_oss
from alarm.page.ding_talk import DingTalk


class ShopAllWeek(BaseCrawl):
    URL = 'https://sycm.taobao.com/adm/v2/downloadBySchema.do?name={}' \
          '&logicType=shop&dimId=1&themeId=1,2,3,4,5,6,7,8,9,10&startDate={}' \
          '&endDate={}&isAutoUpdate=Y&deviceType=0,1,2&indexCode=119,120,121,' \
          '125,126,127,135,136,137,147,148,149,156,157,158,165,166,167,174,' \
          '175,176,183,184,185,192,193,194,201,202,203,210,211,212,219,220,' \
          '221,228,229,230,237,238,239,246,247,248,255,256,257,264,265,266,' \
          '273,274,275,282,283,284,291,292,293,300,301,302,312,313,314,315,' \
          '316,317,327,328,329,336,337,338,343,373,374,379,385,416,418,420,' \
          '520,522,524,591,592,593,603,604,605,609,610,611' \
          '&dateType=week&reportType=1'

    def __init__(self, file_name, start_date, end_date, username, channel, delay_second=None):
        super(ShopAllWeek, self).__init__()
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
            self.crawl_handler_page(ShopAllWeek(self.__file_name,
                                                self.__start_date,
                                                self.__end_date,
                                                self.__username,
                                                self.__channel,
                                                delay_second=DELAY_SECOND))
        else:
            processor_logger.info('拿到了{}的数据'.format(split_name_list[0]))

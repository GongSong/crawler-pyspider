import uuid

from alarm.page.ding_talk import DingTalk
from pyspider.helper.date import Date
from pyspider.libs.base_crawl import *
from backstage_data_migrate.config import *
from backstage_data_migrate.redis_utils import save_to_redis
from cookie.model.data import Data as CookieData
from pyspider.libs.utils import md5string


class SycmTmallTaobaoFlow(BaseCrawl):
    """
    获取生意参谋天猫淘宝的流量来源数据获取
    实时数据
    """
    URL = 'https://sycm.taobao.com/flow/gray/excel.do?_path_=v3/excel/shop/source&device={device}&' \
          'dateType={date_type}&dateRange={start_time}|{end_time}&belong=all' + '#{id}'
    random_id = uuid.uuid4()
    website = 'sycm'
    device_map = {1: 'pc', 2: 'wifi'}

    def __init__(self, device, date_type, start_time, end_time, username, channel, delay_seconds=None):
        super(SycmTmallTaobaoFlow, self).__init__()
        self.__device = device
        self.__delay_seconds = delay_seconds
        self.__date_type = date_type
        self.__start_time = start_time
        self.__end_time = end_time
        self.__username = username
        self.__channel = channel
        self.__channel_name = 'sycm:{}:flow_{}:{}:{}'.format(self.__date_type,
                                                             self.device_map.get(
                                                                 self.__device),
                                                             self.__username,
                                                             self.__start_time)
        self.__url = self.URL.format(device=self.__device,
                                     date_type=self.__date_type,
                                     start_time=self.__start_time,
                                     end_time=self.__end_time,
                                     id=self.random_id)

    def crawl_builder(self):
        builder = CrawlBuilder() \
            .set_url(self.__url) \
            .set_cookies(CookieData.get(CookieData.CONST_PLATFORM_TAOBAO_SYCM, self.__username)) \
            .set_headers_kv('User-Agent', USER_AGENT) \
            .set_task_id(md5string(self.device_map.get(self.__device) + self.__url + self.__username))
        if self.__delay_seconds:
            builder.schedule_delay_second(int(self.__delay_seconds))
        return builder

    def parse_response(self, response, task):
        file_name = '{channel}/{date_type}/{device}/[生意参谋_流量来源]{start_date}--{end_date}.xls'.format(
            channel=self.__channel,
            date_type=self.__date_type,
            device=self.device_map.get(self.__device),
            start_date=self.__start_time,
            end_date=self.__end_time
        )
        # 判断是否抓到了数据, 如果抓不到数据，添加重试次数，直到下午四点
        if 'Content-Disposition' not in response.headers \
            or 'attachment' not in response.headers['Content-Disposition'] \
            or len(response.content) < EMPTY_EXCEL:
            processor_logger.error('cookie error')
            print('cookie error')
            hour = int(Date.now().strftime('%H'))
            if hour > SYCM_TIME:
                # 加上报警
                title = '生意参谋的流量来源数据获取爬虫报警'
                text = '生意参谋的流量来源数据获取爬虫未抓取到 {} 的文件数据，请检查 Mac-Pro 上的 cookie 获取模块'.format(file_name)
                self.crawl_handler_page(DingTalk(OUR_ROBOT_TOKEN, title, text))
                return {
                    'msg': '未获取到今天的数据',
                    'content length': len(response.content),
                }
            return self.crawl_handler_page(
                SycmTmallTaobaoFlow(self.__device, self.__date_type, self.__start_time, self.__end_time,
                                    self.__username, self.__channel, delay_seconds=DELAY_TIME))

        # 保存表格数据到redis
        # save_to_redis(self.__channel_name, response)
        # 保存表格数据到oss
        file_path = oss.get_key(oss.CONST_SYCM_FLOW_PATH, file_name)
        oss.upload_data(file_path, response.content)
        return {
            'msg': '已保存文件: {}'.format(file_path),
            'content length': len(response.content)
        }

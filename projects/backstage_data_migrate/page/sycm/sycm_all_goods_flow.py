from alarm.page.ding_talk import DingTalk
from pyspider.helper.date import Date
from pyspider.libs.base_crawl import *
from backstage_data_migrate.config import *
from cookie.model.data import Data as CookieData
from pyspider.libs.utils import md5string


class SycmAllGoodsFlow(BaseCrawl):
    """
    获取生意参谋 全量商品的流量数据
    实时数据
    """
    URL = 'https://sycm.taobao.com/cc/cockpit/marcro/item/excel/top.json?dateRange={start_date}|{end_date}' \
          '&dateType={date_type}&pageSize=10&page=1&order=desc&orderBy=payAmt&dtUpdateTime=false&keyword=&' \
          'follow=false&cateId=&cateLevel=&guideCateId=&device={device}&indexCode=itmUv,itemCartCnt,payItm' \
          'Cnt,payAmt,payRate'
    website = 'sycm'
    device_map = {
        'all_device': '0',
        'wifi': '2',
    }

    def __init__(self, channel, device, date_type, start_date, end_date, username, delay_seconds=None):
        super(SycmAllGoodsFlow, self).__init__()
        self.__channel = channel
        self.__device = device
        self.__date_type = date_type
        self.__start_date = start_date
        self.__end_date = end_date
        self.__username = username
        self.__delay_seconds = delay_seconds
        self.__url = self.URL.format(start_date=self.__start_date,
                                     end_date=self.__end_date,
                                     date_type=self.__date_type,
                                     device=self.device_map.get(self.__device))

    def crawl_builder(self):
        builder = CrawlBuilder() \
            .set_url(self.__url) \
            .set_cookies(CookieData.get(CookieData.CONST_PLATFORM_TAOBAO_SYCM, self.__username)) \
            .set_headers_kv('User-Agent', USER_AGENT) \
            .set_task_id(md5string(self.device_map.get(self.__device) + self.__url + self.__username))
        if self.__delay_seconds:
            builder.schedule_delay_second(self.__delay_seconds)
        return builder

    def parse_response(self, response, task):
        file_name = '{channel}/全量商品排行/{date_type}/{device}/[生意参谋平台]全量商品排行{start_date}--{end_date}.xls'.format(
            channel=self.__channel,
            date_type=self.__date_type,
            device=self.__device,
            start_date=self.__start_date,
            end_date=self.__end_date
        )
        if 'Content-Disposition' not in response.headers or 'attachment' not in response.headers['Content-Disposition']:
            processor_logger.error('cookie error')
            hour = int(Date.now().strftime('%H'))
            if hour > SYCM_TIME:
                # 加上报警
                title = '生意参谋全量商品排行爬虫报警'
                text = '生意参谋全量商品排行爬虫未抓取到 {} 的文件数据，请检查 Mac-Pro 上的 cookie 获取模块'.format(file_name)
                self.crawl_handler_page(DingTalk(OUR_ROBOT_TOKEN, title, text))
                return {
                    'msg': '未获取到今天的数据',
                    'content': response.content,
                    'content length': len(response.content),
                }
            return self.crawl_handler_page(
                SycmAllGoodsFlow(self.__channel, self.__device, self.__date_type, self.__start_date, self.__end_date,
                                 self.__username, delay_seconds=3600))
        # 保存表格数据到oss
        file_path = oss.get_key(oss.CONST_SYCM_TABLE_FLOW, file_name)
        oss.upload_data(file_path, response.content)
        return {
            'msg': '已保存文件: {}'.format(file_path),
            'content length': len(response.content)
        }

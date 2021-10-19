from pyspider.libs.base_crawl import *
from pyspider.helper.date import Date
from cookie.model.data import Data as CookieData
from taobao_tables_download.config import *
from pyspider.libs.utils import md5string
from alarm.page.ding_talk import DingTalk


class GoodsFlowEntry(BaseCrawl):
    """
    单个商品的 流量来源表格下载 入口
    停止运行（被新的爬虫所替代）
    """

    URL = 'https://sycm.taobao.com/flow/excel.do?_path_=v3/excel/item/source&belong=all&dateType={}&dateRange={}' \
          '&order=desc&orderBy=uv&device={}&itemId={}'

    def __init__(self, client, channel, username, date_type, date_words, date_range, device_type, goods_id, delay=None):
        super(GoodsFlowEntry, self).__init__()
        self.__client = client
        self.__channel = channel
        self.__date_type = date_type
        self.__date_words = date_words
        self.__date_range = date_range
        self.__device_type = device_type
        self.__goods_id = goods_id
        self.__username = username
        self.__delay_second = delay

    def crawl_builder(self):
        builder = CrawlBuilder() \
            .set_url(self.URL.format(self.__date_type,
                                     self.__date_range,
                                     self.__device_type,
                                     self.__goods_id)) \
            .set_cookies(CookieData.get(CookieData.CONST_PLATFORM_TAOBAO_SYCM, self.__username)) \
            .set_headers_kv('User-Agent', USER_AGENT) \
            .set_task_id(md5string('goods_flow_sources' +
                                   str(self.__date_type) +
                                   str(self.__date_range) +
                                   str(self.__device_type) +
                                   str(self.__goods_id) +
                                   str(self.__username)))
        if self.__delay_second:
            builder.schedule_delay_second(self.__delay_second)
        return builder

    def parse_response(self, response, task):
        result = response.content
        file_path = '{}/{}/{}/{}/{}商品流量来源详情-{}.xls'.format(self.__channel, self.__client, self.__date_words,
                                                           self.__goods_id, self.__client, self.__date_range)
        if len(result) < 3000:
            processor_logger.warning('未获取到{}数据'.format(file_path))
            if int(Date.now().strftime('%H')) > UNTIL_HOUR:
                processor_logger.warning('商品的流量来源表格下载失败，请检查 Mac-Pro 上的 cookie 获取模块')
                title = '商品的流量来源表格下载报警'
                text = '商品的流量来源表格下载失败, 未获取到 {} 的文件数据，请检查 Mac-Pro 上的 cookie 获取模块'.format(self.__date_range)
                my_robot_token = 'fc8096a75d4ef6f57a3b83c04e01ed1f87513b9a10ea95d2c09ae13975fe3236'
                self.crawl_handler_page(DingTalk(my_robot_token, title, text))
                return {
                    'error_msg': text,
                    'conten_length': len(result),
                    'content': result,
                }
            self.crawl_handler_page(GoodsFlowEntry(self.__client, self.__channel, self.__username, self.__date_type,
                                                   self.__date_words, self.__date_range, self.__device_type,
                                                   self.__goods_id, delay=DELAY_SECOND))
        else:
            save_path = oss.get_key(oss.CONST_SYCM_GOODS_FLOW_PATH, file_path)
            oss.upload_data(save_path, result)
            return {
                'msg': '已写入文件：{}'.format(file_path),
                'content length': len(result),
            }

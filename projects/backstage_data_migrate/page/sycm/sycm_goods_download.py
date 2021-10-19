import redis

from alarm.page.ding_talk import DingTalk
from backstage_data_migrate.config import *
from mq_handler import CONST_MESSAGE_TAG_TABLE_DOWNLOAD_COMPLETED, CONST_ACTION_UPDATE
from pyspider.helper.date import Date
from pyspider.helper.logging import processor_logger
from pyspider.libs.base_crawl import BaseCrawl
from pyspider.libs.crawl_builder import CrawlBuilder
from cookie.model.data import Data as CookieData
from pyspider.libs.mq import MQ
from pyspider.libs.oss import oss
from pyspider.libs.utils import md5string


class SycmGoods(BaseCrawl):
    """
    生意参谋淘宝，天猫 渠道的商品效果 文件下载
    """
    SYCM_URL = 'https://sycm.taobao.com/bda/download/excel/items/effect/ItemEffectExcel.do?dateRange={0}|{0}' \
               '&dateType=day&orderDirection=false&orderField=itemPv&type=0&device='

    def __init__(self, username, channel, day=1, delay_second=None):
        super(SycmGoods, self).__init__()
        self.__day = day
        self.__yesterday_str = Date.now().plus_days(-self.__day).format(full=False)
        self.__url = self.SYCM_URL.format(self.__yesterday_str)
        self.__username = username
        self.__channel = channel
        self.__delay_second = delay_second

    def crawl_builder(self):
        builder = CrawlBuilder() \
            .set_url(self.__url) \
            .set_cookies(CookieData.get(CookieData.CONST_PLATFORM_TAOBAO_SYCM, self.__username)) \
            .set_headers_kv('User-Agent', USER_AGENT) \
            .schedule_age() \
            .set_task_id(md5string(self.__username + self.__url))
        if self.__delay_second:
            builder.schedule_delay_second(self.__delay_second)
        return builder

    def parse_response(self, response, task):
        content = response.content
        if len(content) < 15000:
            processor_logger.warning('未获取到生意参谋的文件数据')
            if int(Date.now().strftime('%H')) > 16:
                processor_logger.warning('生意参谋下载文件爬虫未抓取到 的文件数据，请检查 Mac-Pro 上的 cookie 获取模块')
                title = '生意参谋下载文件爬虫报警'
                text = '生意参谋下载文件爬虫未抓取到 {} 的文件数据，请检查 Mac-Pro 上的 cookie 获取模块'.format(self.__yesterday_str)
                self.crawl_handler_page(DingTalk(ROBOT_TOKEN, title, text))
                return {
                    'error_msg': text,
                    'content': content
                }
            self.crawl_handler_page(SycmGoods(self.__username, self.__channel, day=self.__day, delay_second=3600))
        else:
            channel_maps = {
                'taobao': '淘宝',
                'tmall': '天猫'
            }
            account_path = '生意参谋' + '_' + channel_maps.get(self.__channel)
            self.save_to_redis('{}_sycm:{}'.format(self.__channel, self.__yesterday_str.replace('-', '')), content)
            file_path = oss.get_key(
                oss.CONST_SYCM_PATH + '{}/'.format(account_path),
                '[生意参谋]商品效果-{start_time}--{end_time}.xls'.format(
                    start_time=self.__yesterday_str,
                    end_time=self.__yesterday_str
                )
            )
            oss.upload_data(file_path, content)

            # 发通知给消息中间件
            data = {
                'channel': SYCM_DOWNLOAD_CHANNEL,
                'file_type': SYCM_DOWNLOAD_FILE_TYPE,
                'file_path': file_path,
                'file_date': self.__yesterday_str,
            }
            MQ().publish_message(CONST_MESSAGE_TAG_TABLE_DOWNLOAD_COMPLETED, data, file_path,
                                 action=CONST_ACTION_UPDATE)

            return {
                'msg': '保存文件成功: {}'.format(account_path),
                'content_length': len(content),
            }

    def save_to_redis(self, name, resp):
        my_redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB_ID)
        self.empty_redis(my_redis, name)
        my_redis.rpush(name, resp)
        processor_logger.info('写入:{}完成'.format(name))

    def empty_redis(self, my_redis, name):
        """
        清空 key 对应的 redis
        :param my_redis:
        :param name:
        :return:
        """
        while True:
            a = my_redis.lpop(name)
            if a is not None:
                processor_logger.warning('pop {}'.format(name))
                continue
            else:
                break

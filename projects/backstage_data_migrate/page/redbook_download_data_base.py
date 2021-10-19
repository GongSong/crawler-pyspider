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


class RedbookDownloadBase(BaseCrawl):
    """
    小红书渠道的 商品流量表格下载
    """

    def __init__(self, data_url, username, day, channel, delay_second=None):
        super(RedbookDownloadBase, self).__init__()
        self.__username = username
        self.__delay_second = delay_second
        self.__day = day
        self.__channel = channel
        self.__yesterday_str = Date.now().plus_days(-self.__day).format(full=False)
        self.__origin_url = data_url
        self.__final_url = self.__origin_url.format(self.__yesterday_str)

    def crawl_builder(self):
        cookies_dict_trans = {}
        cookies_dict = [i.strip().split('=', 1) for i in
                        CookieData.get(CookieData.CONST_PLATFORM_REDBOOK, self.__username).split(';')]
        for cookie in cookies_dict:
            cookies_dict_trans[cookie[0]] = cookie[1]
        builder = CrawlBuilder() \
            .set_url(self.__final_url) \
            .set_cookies_dict(cookies_dict_trans) \
            .set_headers_kv('User-Agent', USER_AGENT) \
            .schedule_age() \
            .set_task_id(md5string(self.__username + self.__final_url))
        if self.__delay_second:
            builder.schedule_delay_second(self.__delay_second)
        return builder

    def parse_response(self, response, task):
        content = response.content
        if (len(content) < 260 and self.__channel == REDBOOK_SHOP_TYPE) or (
            len(content) < 930 and self.__channel == REDBOOK_GOODS_TYPE):
            processor_logger.warning('未获取到 小红书{} 的文件数据'.format(self.__channel))
            if int(Date.now().strftime('%H')) > 16:
                processor_logger.warning('小红书渠道的 商品流量表格下载未抓取到 {}文件数据，请检查线上的 cookie 获取模块'.format(self.__channel))
                title = '小红书下载文件爬虫报警'
                text = '小红书下载文件爬虫未抓取到 {} 的文件数据，请检查线上的 cookie 获取模块'.format(self.__yesterday_str + self.__channel)
                self.crawl_handler_page(DingTalk(ROBOT_TOKEN, title, text))
                return {
                    'content length': len(content),
                    'error_msg': text,
                    'url': self.__final_url
                }
            self.crawl_handler_page(
                RedbookDownloadBase(self.__origin_url, self.__username, self.__day, self.__channel, delay_second=3600))
        else:
            if self.__channel == REDBOOK_GOODS_TYPE:
                redis_path = 'redbook:{}'.format(self.__yesterday_str.replace('-', ''))
            else:
                redis_path = 'redbook:shop:{}'.format(self.__yesterday_str.replace('-', ''))
            self.save_to_redis(redis_path, content)
            account_path = '{channel}({file_date}_{file_date}).csv'.format(channel=self.__channel,
                                                                           file_date=self.__yesterday_str)
            file_path = oss.get_key(oss.CONST_REDBOOK_DATA_PATH, account_path)
            oss.upload_data(file_path, content)

            # 发通知给消息中间件
            data = {
                'channel': REDBOOK_DOWNLOAD_CHANNEL,
                'file_type': REDBOOK_DOWNLOAD_FILE_TYPE,
                'file_path': file_path,
                'file_date': self.__yesterday_str,
            }
            MQ().publish_message(CONST_MESSAGE_TAG_TABLE_DOWNLOAD_COMPLETED, data, file_path,
                                 action=CONST_ACTION_UPDATE)

            processor_logger.info('成功写入: {} 到oss'.format(account_path))
            return {
                'content length': len(content),
                'msg': '已写入小红书的商品和店铺文件',
                'date': self.__yesterday_str,
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

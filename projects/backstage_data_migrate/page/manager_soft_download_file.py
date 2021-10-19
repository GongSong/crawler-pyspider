from pyspider.helper.logging import processor_logger
from pyspider.libs.oss import oss
from backstage_data_migrate.config import *
from pyspider.helper.date import Date
from pyspider.libs.base_crawl import BaseCrawl
from pyspider.libs.crawl_builder import CrawlBuilder
from pyspider.libs.utils import md5string


class ManagerSoftDownFile(BaseCrawl):
    """
    掌柜软件的商品的导出表格上传
    """

    def __init__(self, url, compare_words, channel):
        """
        掌柜软件的商品的导出表格上传
        :param url: 表格下载地址
        :param compare_words: 用于参照导出商品的类型
        :param channel: 保存数据的渠道（店铺）
        """
        super(ManagerSoftDownFile, self).__init__()
        self.__url = url
        self.__compare_words = compare_words
        self.__channel = channel

    def crawl_builder(self):
        builder = CrawlBuilder() \
            .set_url(self.__url) \
            .set_headers_kv('User-Agent', USER_AGENT) \
            .set_task_id(md5string(self.__url))
        return builder

    def parse_response(self, response, task):
        if 'Content-Type' not in response.headers or 'sheet' not in response.headers['Content-Type']:
            processor_logger.error('cookie error')
            assert False, 'cookie 过期'
        start_time = Date.now().format(full=False)
        end_time = Date.now().format(full=False)
        file_path = oss.get_key(
            oss.CONST_TAOBAO_MANAGER_SOFT_PATH,
            '{channel}/{words}/掌柜软件:{start_time}--{end_time}.xls'.format(
                channel=self.__channel,
                words=self.__compare_words.split('，', 1)[0],
                start_time=start_time,
                end_time=end_time
            )
        )
        oss.upload_data(file_path, response.content)
        return {
            'url': response.url,
            'excelSize': len(response.content),
            'file_path': file_path,
            'channel': self.__channel
        }

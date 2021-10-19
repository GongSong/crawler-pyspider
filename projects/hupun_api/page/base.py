from pyspider.helper.date import Date
from pyspider.libs.base_crawl import *
from alarm.page.ding_talk import DingTalk
from urllib.parse import quote_plus


class Base(BaseCrawl):
    """
    hupun api 接口基类
    """

    def __init__(self, path, post_data=None):
        """
        文档：https://open-api.hupun.com/api/doc/erp
        :param path:
        """
        super(Base, self).__init__()
        self._path = path
        self._post_data = {} if not post_data else post_data

    def set_param(self, key, value):
        """
        设置参数
        :param key:
        :param value:
        :return:
        """
        self._post_data[key] = value
        return self

    def crawl_builder(self):
        self._post_data.setdefault('_app', config.get('hupun', 'key'))
        self._post_data.setdefault('_t', Date.now().timestamp())
        if config.get('hupun', 's'):
            self._post_data.setdefault('_s', config.get('hupun', 's'))
        arr = []

        # 签名
        for _ in sorted(self._post_data.keys()):
            arr.append('='.join([_, quote_plus(str(self._post_data.get(_)))]))
        arr.append(
            '_sign=' + md5string(config.get('hupun', 'secret') + ('&'.join(arr)) + config.get('hupun', 'secret')))

        return CrawlBuilder() \
            .set_url(config.get('hupun', 'gateway') + self._path) \
            .set_task_id(self.get_unique_define()) \
            .set_headers_kv('Content-Type', 'application/x-www-form-urlencoded;charset=utf-8') \
            .set_post_data('&'.join(arr))

    @abc.abstractmethod
    def get_unique_define(self):
        """
        :return:
        """
        return ''

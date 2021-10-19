import json
from cookie.config import HUPUN_COOKIE_POOL_KEY
from pyspider.helper.date import Date
from pyspider.helper.string import merge_str, json_loads
from pyspider.libs.base_crawl import *
from xml.etree.ElementTree import XML
from cookie.model.data import Data as CookieData
import random


class Base(BaseCrawl):
    PATH = '/dorado/view-service'
    # 第一优先级
    CONST_PRIORITY_FIRST = 50
    # 第二优先级
    CONST_PRIORITY_SECOND = 40
    # 第三优先级
    CONST_PRIORITY_THIRD = 30
    # 捆绑的最优先
    CONST_PRIORITY_BUNDLED = 100
    # 目前是类目抓取的最优先
    CONST_PRIORITY_TOP = 110

    def __init__(self):
        super(Base, self).__init__()
        self._priority = 0
        self._page = 1
        self._page_size = 100
        self._start_time = None
        self._end_time = None
        self._retries = 3
        self._age = None
        self._delay_seconds = 0
        self._cookies_position = 0  # 在配置文件中读取账号的位置，默认为第0个
        self._use_cookie_pool = False  # 是否使用万里牛cookie池中的cookie
        self._proxy = None  # 是否使用IP代理

    def set_age(self, age):
        """
        设置多少时间内不重复抓取数据
        :param age:
        :return:
        """
        self._age = age
        return self

    def set_priority(self, priority):
        """
        优先级
        :param priority:
        :return:
        """
        self._priority = priority
        return self

    def set_page(self, page):
        """
        第几页
        :param page:
        :return:
        """
        self._page = page
        return self

    def set_page_size(self, page_size):
        """
        一页多少条
        :param page_size:
        :return:
        """
        self._page_size = page_size
        return self

    def set_start_time(self, start_time):
        """
        开始时间
        :param start_time:
        :return:
        """
        self._start_time = start_time
        return self

    def set_end_time(self, end_time):
        """
        结束时间
        :param end_time:
        :return:
        """
        self._end_time = end_time
        return self

    def set_retries(self, retries):
        """
        结束时间
        :param retries:
        :return:
        """
        self._retries = retries
        return self

    def set_delay_seconds(self, seconds):
        """
        设置延时请求的时间
        :param seconds:
        :return:
        """
        self._delay_seconds = seconds
        return self

    def set_cookie_position(self, position: int):
        """
        设置获取hupun cookie 的账号位置, 默认获取第0个
        :param position: 账号位置
        :return:
        """
        self._cookies_position = int(position)
        return self

    def set_proxy(self, proxy: str):
        """
        使用IP代理
        :param proxy:
        :return:
        """
        self._proxy = proxy
        return self

    @staticmethod
    def detect_xml_text(text, handle=False):
        for _el in XML(text).iter('response'):
            return json_loads(_el.text, handle)

    def get_cookie(self) -> str:
        """
        获取万里牛cookie。如果使用cookie池，则从cookie池获取；如果获取不成功，还是用cookie_position方式获取。
        如果不用cookie池，直接用cookie_position方式获取。
        :return:
        """
        if self._use_cookie_pool:
            cookies_keys = default_storage_redis.keys(HUPUN_COOKIE_POOL_KEY + '*')
            cookies_key = random.choice(cookies_keys).decode('utf8')
            pool_cookie = default_storage_redis.get(cookies_key)
            cookies = pool_cookie if pool_cookie else CookieData.get(
                CookieData.CONST_PLATFORM_HUPUN, CookieData.CONST_USER_HUPUN[self._cookies_position][0])
        else:
            cookies = CookieData.get(CookieData.CONST_PLATFORM_HUPUN,
                                     CookieData.CONST_USER_HUPUN[self._cookies_position][0])

        return cookies

    def use_cookie_pool(self, use_pool=True):
        """
        使用万里牛cookie池中的cookie，优先度高于set_cookie_position方法
        :param use_pool: 是否使用cookie池, 默认使用
        :return:
        """
        self._use_cookie_pool = use_pool
        return self

    def crawl_builder(self):
        unique_define = self.get_unique_define()
        cookies = self.get_cookie()
        # print(cookies)
        crawl_builder = CrawlBuilder() \
            .set_url('{service_host}{path}#{unique}'.format(
                service_host=config.get('hupun', 'service_host'),
                path=self.PATH,
                unique=unique_define)) \
            .schedule_priority(self._priority) \
            .set_headers_kv('Content-Type', 'text/xml') \
            .set_cookies(cookies if cookies else {}) \
            .set_post_data(self.get_request_data()) \
            .schedule_retries(self._retries)
        if unique_define:
            crawl_builder.set_task_id(md5string(unique_define))
        if self._age:
            crawl_builder.schedule_age(self._age)
        if self._delay_seconds:
            crawl_builder.schedule_delay_second(self._delay_seconds)
        if self._proxy:
            crawl_builder.set_proxy(self._proxy)
        return crawl_builder

    @abc.abstractmethod
    def get_request_data(self):
        """
        请求体
        :return:
        """
        pass

    @abc.abstractmethod
    def get_unique_define(self):
        """
        :return:
        """
        return ''

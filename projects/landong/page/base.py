from cookie.config import LANDONG_COOKIE_POOL_KEY
from landong.config import USER_AGENT
from pyspider.libs.base_crawl import *
from cookie.model.data import Data as CookieData
import random

"""
澜东云基类
"""


class Base(BaseCrawl):
    # 数值越大，优先级越高
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
        self._priority = 60
        self._page = 1
        self._limit = 100
        self._retries = 3
        self._age = None
        self._delay_seconds = 0
        self._use_cookie_pool = False  # 是否使用cookie池中的cookie
        self._cookies_position = 0
        self._proxy = None  # 是否使用IP代理
        self._host = "service_host"

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
        self._limit = page_size
        return self

    def set_retries(self, retries):
        """
        重试次数
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

    def set_proxy(self, proxy: str):
        """
        使用IP代理
        :param proxy:
        :return:
        """
        self._proxy = proxy
        return self

    def set_cookie_position(self, position):
        """
        制定获取第几个账号的cookie
        :param position:
        :return:
        """
        self._cookies_position = position
        return self

    def set_crawl_host(self, host: str):
        """
        设置抓取页面的host
        :param host:
        :return:
        """
        self._host = host
        return self

    def get_cookie(self) -> str:
        """
        获取cookie。如果使用cookie池，则从cookie池获取；如果获取不成功，还是用cookie_position方式获取。
        如果不用cookie池，直接用cookie_position方式获取。
        :return:
        """
        if self._use_cookie_pool:
            cookies_keys = default_storage_redis.keys(LANDONG_COOKIE_POOL_KEY + '*')
            cookies_key = random.choice(cookies_keys).decode('utf8')
            pool_cookie = default_storage_redis.get(cookies_key)
            cookies = pool_cookie if pool_cookie else CookieData.get(
                CookieData.CONST_PLATFORM_LANDONG, CookieData.CONST_USER_LANDONG[self._cookies_position][0])
        else:
            cookies = CookieData.get(CookieData.CONST_PLATFORM_LANDONG,
                                     CookieData.CONST_USER_LANDONG[self._cookies_position][0])

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
        crawl_builder = CrawlBuilder() \
            .set_url('{service_host}{path}#{unique}'.format(
            service_host=config.get('landong', self._host),
            path=self.get_api_route(),
            unique=unique_define)) \
            .schedule_priority(self._priority) \
            .set_cookies(cookies if cookies else {}) \
            .set_headers_kv('User-Agent', USER_AGENT) \
            .schedule_retries(self._retries)
        if self.get_post_data():
            crawl_builder.set_post_data(self.get_post_data())
        if unique_define:
            crawl_builder.set_task_id(md5string(unique_define))
        if self._age:
            crawl_builder.schedule_age(self._age)
        if self._delay_seconds:
            crawl_builder.schedule_delay_second(self._delay_seconds)
        if self._proxy:
            crawl_builder.set_proxy(self._proxy)
        return crawl_builder

    def get_post_data(self):
        """
        构建post参数
        :return:
        """
        return ""

    @abc.abstractmethod
    def get_api_route(self):
        """
        设置目标数据的接口路由地址
        :return:
        """
        pass

    @abc.abstractmethod
    def get_unique_define(self):
        """
        设置当前爬虫的唯一标识
        :return:
        """
        return ''

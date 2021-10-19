from pyspider.libs.base_crawl import *
from cookie.config import *


class UpdateOldCookie(BaseCrawl):
    """
    更新老 hupun 的 cookie
    """

    URL = 'http://10.0.5.58:7901/cookies'

    def __init__(self, cookie_str, priority=0):
        super(UpdateOldCookie, self).__init__()
        self.__cookie_str = cookie_str
        self.__priority = priority

    def crawl_builder(self):
        post_data = {
            'website': 'hupun',
            'username': '万里牛:测试',
            'data': self.__cookie_str,
        }
        builder = CrawlBuilder() \
            .set_url(self.URL) \
            .set_headers_kv('User-Agent', USER_AGENT) \
            .schedule_priority(self.__priority) \
            .set_post_json_data(post_data) \
            .set_task_id(md5string(self.__cookie_str))

        return builder

    def parse_response(self, response, task):
        return {
            'response': response.content,
            'cookie_str': self.__cookie_str
        }

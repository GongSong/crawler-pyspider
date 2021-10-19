import json

from blog_spider.config import *
from blog_spider.page.weibo_blogger import WeiboBlogger
from blog_spider.page.weibo_blogger_result import WeiboBloggerRlt
from pyspider.helper.string import merge_str
from pyspider.libs.base_crawl import *
from pyspider.helper.ips_pool import IpsPool


class WeiboBloggerIdRlt(BaseCrawl):
    """
    构造微博博主信息前的 container ID 的获取 result
    """

    URL = 'https://m.weibo.cn/api/container/getIndex?type=uid&value={}'

    def __init__(self, blogger_id, use_proxy=True, priority=0, to_next_page=False, queue_data=''):
        super(WeiboBloggerIdRlt, self).__init__()
        self.__priority = priority
        self.__blogger_id = blogger_id
        self.__use_proxy = use_proxy
        self.__to_next_page = to_next_page
        self.__queue_data = queue_data

    def crawl_builder(self):
        builder = CrawlBuilder() \
            .set_url(self.URL.format(self.__blogger_id)) \
            .set_headers_kv('User-Agent', USER_AGENT) \
            .schedule_priority(self.__priority) \
            .set_task_id(merge_str(self.__blogger_id, self.__priority))

        if self.__use_proxy:
            builder.set_proxy(IpsPool.get_ip_from_pool())

        return builder

    def parse_response(self, response, task):
        text = response.text
        js_text = json.loads(text)
        container_id = ''
        container_tabs = js_text['data']['tabsInfo']['tabs']
        for tab in container_tabs:
            if tab.get('tabKey') == 'weibo':
                container_id = tab.get('containerid')
        assert container_id, '获取博主: {} 的container ID 失败'.format(self.__blogger_id)
        for i in range(1, 16):
            print('开始获取第: {} 页的数据'.format(i))
            self.catch_next_page(container_id, i)

    def catch_next_page(self, container_id, page, retry=3):
        try:
            blogger_url = 'https://m.weibo.cn/api/container/getIndex?type=uid&value={blogger_id}&containerid={con_id}'.format(
                blogger_id=self.__blogger_id, con_id=container_id)
            WeiboBloggerRlt(blogger_url, page=page, to_next_page=self.__to_next_page, priority=self.__priority,
                            queue_data=self.__queue_data).get_result()
        except Exception as e:
            print('WeiboBloggerIdRlt error: {}'.format(e))
            if retry > 0:
                self.catch_next_page(container_id, page, retry - 1)
            return

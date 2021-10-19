from crawl_taobao_goods_migrate.model.task import Task
from pyspider.libs.base_crawl import *


class BaseCallback(BaseCrawl):
    """
    回调链接基类
    """
    def __init__(self, url, callback_name, priority=1):
        super(BaseCallback, self).__init__()
        self.__url = url
        self.__name = callback_name
        self.__priority = priority

    def crawl_builder(self):
        return CrawlBuilder() \
            .set_url(self.__url) \
            .schedule_age() \
            .schedule_priority(self.__priority) \
            .set_task_id(Task.get_task_id(self.__name, self.__url))

    def parse_response(self, response, task):
        return {
            'url': response.url,
            'content': response.text,
            'callback_name': self.__name,
            'excelSize': len(response.content),
        }

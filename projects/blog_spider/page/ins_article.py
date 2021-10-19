import re
from copy import deepcopy
from blog_spider.config import *
from blog_spider.model.es.blog_result import BlogResult
from pyspider.helper.string import merge_str
from pyspider.libs.base_crawl import *
from pyspider.helper.ips_pool import IpsPool
from pyspider.helper.date import Date


class InsArticle(BaseCrawl):
    """
    抓取微博内容详情
    """
    URL = 'https://www.instagram.com/p/{}/'

    def __init__(self, content_id, data, use_proxy=False, priority=0):
        super(InsArticle, self).__init__()
        self.__content_id = content_id
        self.__url = self.URL.format(self.__content_id)
        self.__data = deepcopy(data)
        self.__use_proxy = use_proxy
        self.__priority = priority

    def crawl_builder(self):
        builder = CrawlBuilder() \
            .set_url(self.__url) \
            .set_headers_kv('User-Agent', USER_AGENT) \
            .set_timeout(GOODS_TIMEOUT) \
            .set_connect_timeout(GOODS_CONNECT_TIMEOUT) \
            .schedule_priority(self.__priority) \
            .set_task_id(md5string(merge_str(self.__url[-16:], self.__priority)))

        if self.__use_proxy:
            builder.set_proxy(OUT_PROXY)

        return builder

    def parse_response(self, response, task):
        content = response.text
        print('content: {}'.format(content))

        # # 标记是否发送es更新
        # # send_es_update = False
        # # 过滤文本的html标签
        # article_text = content.split('$render_data = [{', 1)[1].split('"text": "', 1)[1].split('",', 1)[0]
        # html_filter_str = re.sub(r'<[^>]+>', "", article_text, re.S)
        # # 关键词
        # # content_type = int(self.__data.get('content_type'))
        # # keywords = self.__data.get('keywords')
        # # if content_type == 1:
        # #     if keywords:
        # #         for words in keywords:
        # #             if words in article_text:
        # #                 send_es_update = True
        # #     else:
        # #         send_es_update = True
        # # elif content_type == 2:
        # #     send_es_update = True
        # # 爬虫抓取时间
        # create_time = Date.now().timestamp()
        # # 更新内容和爬虫抓取时间
        # self.__data['content'] = html_filter_str
        # self.__data['create_time'] = create_time
        #
        # # if send_es_update:
        # BlogResult().update([self.__data], async=True)
        #
        # return {
        #     'unique_name': 'weibo_article',
        #     'preview_data': self.__data,
        #     'content': content
        # }

from copy import deepcopy

from blog_spider.config import PRIORITY_HIGHEST, PRIORITY_FIRST
from blog_spider.model.es.blogger_msg import BlogMsg
from blog_spider.page.weibo_blogger_id import WeiboBloggerId
from blog_spider.page.weibo_topic import WeiboTopic
from mq_handler.base import Base
from pyspider.helper.date import Date


class BlogSyncAct(Base):
    """
    同步微博和ins的账号;
    数据抓取入口;
    """

    def execute(self):
        print('同步微博和ins的账号, 数据抓取入口;')
        self.print_basic_info()
        data = self._data

        # 抓取入口
        self.catch_entry(data)

    def catch_entry(self, data):
        """
        保存微博和ins的账号以及下发抓取任务
        :param data:
        :return:
        """
        account_key = data.get('accountKey')
        keywords = data.get('keywords')
        account_type = data.get('type')
        status = data.get('status', 2)
        content_type = data.get('contentType', 0)

        # 处理keywords
        if keywords and isinstance(keywords, list):
            for _i, _k in enumerate(keywords):
                keywords[_i] = _k.strip()

        # 爬虫的抓取时间
        sync_time = Date.now().format_es_utc_with_tz()
        if content_type == 1:
            if account_type == 1 and int(status) == 1:
                # 抓取博主的内容
                WeiboBloggerId(account_key, priority=PRIORITY_HIGHEST, to_next_page=True,
                               queue_data=deepcopy(data)).enqueue()
            elif account_type == 2 and int(status) == 1:
                # 抓取ins的内容
                pass
            # 保存账号信息
            msg = [{
                'account_key': account_key,
                'keywords': keywords,
                'data_type': account_type,
                'status': status,
                'content_type': content_type,
                'sync_time': sync_time,
            }]
            BlogMsg().update(msg, async=True)
        elif content_type == 2 and isinstance(keywords, list):
            # 抓取关键词
            for words in keywords:
                WeiboTopic(words, priority=PRIORITY_FIRST, to_next_page=True, queue_data=deepcopy(data)).enqueue()

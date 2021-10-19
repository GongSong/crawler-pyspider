import unittest

from blog_spider.config import *
from blog_spider.page.ins_blogger import InsBlogger
from blog_spider.page.weibo_article import WeiboArticle
from blog_spider.page.weibo_blogger import WeiboBlogger
from blog_spider.page.weibo_blogger_id import WeiboBloggerId
from blog_spider.page.weibo_topic import WeiboTopic


class Test(unittest.TestCase):

    def test_weibo_topic(self):
        words = '陪你温暖过冬'
        data = {'type': 1, 'keywords': ['陪你温暖过冬'], 'contentType': 2}
        WeiboTopic(words, use_proxy=False, to_next_page=True, queue_data=data).get_result()

    def _test_weibo_article(self):
        url = 'https://m.weibo.cn/detail/4360684710548959'
        data = {'data_type': 1}
        assert WeiboArticle(url, data).test()

    def _test_weibo_blog_id(self):
        blogger_id = '1969176463'
        assert WeiboBloggerId(blogger_id, priority=PRIORITY_FIRST).test()

    def _test_weibo_blog(self):
        url = 'https://m.weibo.cn/api/container/getIndex?type=uid&value=1969176463&containerid=1076031969176463'
        assert WeiboBlogger(url, priority=PRIORITY_FIRST).test()

    def _test_ins_blogger(self):
        InsBlogger().test()


if __name__ == '__main__':
    unittest.main()

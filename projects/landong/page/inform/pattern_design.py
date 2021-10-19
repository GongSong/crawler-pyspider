from pyspider.helper.date import Date
from pyspider.libs.base_crawl import *


class PatternDesignInform(BaseCrawl):
    PATH = "/internal.php?method=goods.saveDesign"

    def __init__(self, post_data: dict):
        """
        新增或编辑 新款档案-商品设计 时通知天鸽
        :param post_data: post 参数
        """
        super(PatternDesignInform, self).__init__()
        self.post_data = post_data

    def crawl_builder(self):
        return CrawlBuilder() \
            .set_url(config.get("tg", "host") + "{}#{}".format(self.PATH, self.post_data.get("uuid", ""))) \
            .set_post_json_data(self.post_data) \
            .schedule_priority(0)

    def parse_response(self, response, task):
        return {
            'request post_data': self.post_data,
            'responseSize': len(response.content),
            'result': response.json
        }

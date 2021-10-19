from pyspider.libs.base_crawl import *
from pyspider.helper.date import Date


class BasPatternCategoryInform(BaseCrawl):
    PATH = "/internal.php?method=SystemSetting.updateCategory"

    def __init__(self, data):
        """
        新增或编辑品类时通知天鸽
        """
        super(BasPatternCategoryInform, self).__init__()
        self.data = {
            "list": data
        }

    def crawl_builder(self):
        return CrawlBuilder() \
            .set_url(config.get("tg", "host") + "{}#{}".format(self.PATH, Date().now().millisecond())) \
            .set_post_json_data(self.data)

    def parse_response(self, response, task):
        return {
            'data': self.data,
            'result': response.json
        }

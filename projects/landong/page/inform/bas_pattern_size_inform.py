from pyspider.libs.base_crawl import *
from pyspider.helper.date import Date


class BasPatternSizeInform(BaseCrawl):
    PATH = "/internal.php?method=systemSetting.updateSize"

    def __init__(self, data):
        """
        新增或编辑尺码时通知天鸽
        """
        super(BasPatternSizeInform, self).__init__()
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

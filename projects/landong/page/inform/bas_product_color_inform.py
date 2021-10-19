from pyspider.helper.date import Date
from pyspider.libs.base_crawl import *


class BasProductColorInform(BaseCrawl):
    PATH = "/internal.php?method=SystemSetting.UpdateColor"

    def __init__(self, post_data: dict):
        """
        新增或编辑颜色档案时通知天鸽
        :param post_data: post 参数
        """
        super(BasProductColorInform, self).__init__()
        self.post_data = post_data

    def crawl_builder(self):
        return CrawlBuilder() \
            .set_url(config.get("tg", "host") + "{}#{}".format(self.PATH, Date.now().millisecond())) \
            .set_post_json_data(self.post_data)

    def parse_response(self, response, task):
        return {
            'request post_data': self.post_data,
            'responseSize': len(response.content),
            'result': response.json
        }

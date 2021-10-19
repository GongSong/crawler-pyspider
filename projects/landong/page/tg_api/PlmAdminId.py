from pyspider.libs.base_crawl import *


class PlmAdminId(BaseCrawl):
    PATH = "/internal.php?method=admin.getAdminInfo"

    def __init__(self, name):
        """
        根据名字获取天鸽系统的人员ID
        """
        super(PlmAdminId, self).__init__()
        self.name = name

    def crawl_builder(self):
        return CrawlBuilder() \
            .set_url(config.get("tg", "host") + "{}#{}".format(self.PATH, self.name)) \
            .set_post_data_kv("name", self.name)

    def parse_response(self, response, task):
        return {
            'name': self.name,
            'result': response.json,
        }

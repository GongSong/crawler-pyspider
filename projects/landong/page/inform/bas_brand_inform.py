from pyspider.libs.base_crawl import *


class BasBrandInform(BaseCrawl):
    PATH = "/internal.php?method=band.updateBand"

    def __init__(self, code, name, status, creator, create_time):
        """
        新增或编辑波段时通知天鸽
        :param code: 编码
        :param name: 名称
        :param status: 0: 停用, 1: 启用
        :param creator: 创建人
        :param create_time: 创建时间
        """
        super(BasBrandInform, self).__init__()
        self.code = code
        self.name = name
        self.status = status
        self.creator = creator
        self.creator = creator
        self.create_time = create_time
        self.data = {
            "code": self.code,
            "name": self.name,
            "status": self.status,
            "creator": self.creator,
            "createTime": self.create_time,
        }

    def crawl_builder(self):
        return CrawlBuilder() \
            .set_url(config.get("tg", "host") + "{}#{}".format(self.PATH, self.name)) \
            .set_post_data(self.data)

    def parse_response(self, response, task):
        return {
            'data': self.data,
            'responseSize': len(response.content),
            'result': response.json
        }

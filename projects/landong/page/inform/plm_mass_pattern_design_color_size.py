from pyspider.libs.base_crawl import *
from pyspider.helper.date import Date


class PlmMassPatternDesignColorSizeInform(BaseCrawl):
    PATH = "/internal.php?method=goods.updateSkuBarcode"

    def __init__(self, design_code, data):
        """
        新增或编辑商品档案的商品编码， 通知天鸽
        """
        super(PlmMassPatternDesignColorSizeInform, self).__init__()
        self.design_code = design_code
        self.data = {
            "designCode": design_code,
            "list": data
        }

    def crawl_builder(self):
        return CrawlBuilder() \
            .set_url(config.get("tg", "host") + "{}#{}".format(self.PATH, self.design_code)) \
            .set_post_json_data(self.data)

    def parse_response(self, response, task):
        return {
            'data': self.data,
            'result': response.json
        }

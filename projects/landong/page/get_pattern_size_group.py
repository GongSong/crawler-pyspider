from landong.page.bas_pattern_size import BasPatternSize
from landong.page.base import Base
from pyspider.helper.date import Date


class GetPatternSizeGroup(Base):
    """
    澜东 尺码组
    """

    PATH = "/Bas/PatternSizeGroup/GetPatternSizeGroupTreeNode"

    def __init__(self):
        super(GetPatternSizeGroup, self).__init__()

    def get_api_route(self):
        return self.PATH

    def get_unique_define(self):
        return ":".join([self.PATH, str(self._page), str(Date().now().timestamp())])

    def parse_response(self, response, task):
        """
        解析相应数据
        """
        content = response.json
        data = content.get("children", [])

        for node in data:
            self.crawl_handler_page(BasPatternSize(node=node.get("id"), next_page=True).set_crawl_host("page_host"))

        return {
            "nodes": data,
        }


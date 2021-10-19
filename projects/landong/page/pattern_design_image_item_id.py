from landong.page.base import Base
from landong.page.pattern_design_image import PatternDesignImage
from pyspider.config import config
from pyspider.helper.date import Date


class PatternDesignImageItemId(Base):
    """
    新款档案详情的图片 - 获取图片接口里的 item_id
    """

    PATH = "/Plm/ArtWork/Edit"

    def __init__(self, post_data: dict):
        super(PatternDesignImageItemId, self).__init__()
        self.post_data = post_data
        self.uuid = post_data.get("uuid", "")

    def get_api_route(self):
        return self.PATH + "?containerId=Plm_PatternDesignProp_1277553577-RightFormContainer&uuid={}" \
                           "&organizationId={}".format(self.uuid, config.get("landong", "organization_id"))

    def get_unique_define(self):
        return ":".join([self.PATH, str(self._page), self.post_data.get("uuid", "")])

    def parse_response(self, response, task):
        content = response.text
        if "ArtWorkImageIndex" in content:
            image_path = content.split("ArtWorkImageIndex", 1)[1].split("\"}", 1)[0].strip()
            self.crawl_handler_page(PatternDesignImage(image_path, self.post_data, True).set_priority(
                PatternDesignImage.CONST_PRIORITY_SECOND))

        # 解析响应
        return {
            "response": response.text[:200]
        }

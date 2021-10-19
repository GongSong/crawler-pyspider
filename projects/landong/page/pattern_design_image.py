from common_crawler.page.image_download import ImageDownload
from landong.page.base import Base
from landong.page.pattern_design_sizes import PatternDesignSizes
from pyspider.config import config
from pyspider.helper.date import Date
from pyspider.libs.oss import oss_cdn


class PatternDesignImage(Base):
    """
    新款档案详情的图片 - 获取 图稿 标签里最新图稿的商品图片
    """

    PATH = "/Plm/ArtWork/GetBillItemImageList"

    def __init__(self, image_path, post_data: dict, next_page=False):
        super(PatternDesignImage, self).__init__()
        self.post_data = post_data
        self.next_page = next_page
        self.image_path = image_path
        self.item_id = image_path.split("billId=", 1)[1].split("&", 1)[0]

    def get_post_data(self):
        data = {
            "page": self._page,
            "limit": self._limit,
            "start": (self._page - 1) * self._limit if self._page > 0 else 0,
        }
        return data

    def get_api_route(self):
        return self.PATH + self.image_path

    def get_unique_define(self):
        return ":".join([self.PATH, str(self._page), self.post_data.get("uuid", "")])

    def parse_response(self, response, task):
        content = response.json
        data = content.get("data", [])
        total = content.get("total", 0)
        origin_img_name = ""

        if self.post_data.get("imgs", []):
            origin_img_name = self.post_data.get("imgs", [])[0].split("/")[-1].split(".")[0]

        # 获取详情图
        images = []
        for item in data:
            store_name = item.get("StoreName", "")
            store_path = item.get("StorePath", "").replace("\\", "%5C")
            img_url = "https://v3.ldyerp.com/Plm/ArtWork/Thumb?name={}&width=500&height=500&imageDirectory={}".format(
                store_name, store_path)
            # 图片上传到oss
            oss_img_path = oss_cdn.get_key(oss_cdn.CONST_LANDONG_IMAGE, store_name)
            self.crawl_handler_page(ImageDownload(img_url, oss_img_path, self.get_cookie()))
            img = "https://{bucket_name}.{endpoint}/{oss_img_path}".format(
                bucket_name=config.get("oss_cdn", "bucket_name"),
                endpoint=config.get("oss_cdn", "endpoint"),
                oss_img_path=oss_img_path)
            # 去掉图片地址里的 -internal 字段
            img = img.replace("-internal", "")
            if origin_img_name and store_name.split(".")[0] in origin_img_name:
                # 过滤掉在列表页抓取的主图
                continue
            images.append(img)

        self.post_data["imgs"] += images

        # 获取尺码列表
        self.crawl_handler_page(PatternDesignSizes(self.item_id, self.post_data))

        # 抓取下一页
        if self.next_page and total > self._limit * self._page:
            self.crawl_handler_page(
                PatternDesignImage(self.image_path, self.post_data, self.next_page).set_page(self._page + 1))

        # 解析响应
        return {
            "response": response.text[:200],
            "item_id": self.item_id
        }

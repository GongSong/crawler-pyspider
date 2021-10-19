from common_crawler.page.image_download import ImageDownload
from landong.config import brand_map, design_source_map, unit_map
from landong.model.es.bas_brand import BasBrandEs
from landong.model.es.bas_product_category import BasProductCategoryEs
from landong.model.es.pattern_design import PatternDesignEs
from landong.page.base import Base
from landong.page.pattern_design_image_item_id import PatternDesignImageItemId
from landong.page.tg_api.PlmAdminId import PlmAdminId
from pyspider.config import config
from pyspider.helper.date import Date
from pyspider.libs.oss import oss_cdn


class PatternDesign(Base):
    """
    新款档案 - 新增编辑商品设计
    """

    PATH = "/Plm/PatternDesign/PagedQuery"

    def __init__(self, next_page=False):
        super(PatternDesign, self).__init__()
        self.next_page = next_page

    def get_post_data(self):
        data = {
            "page": self._page,
            "limit": self._limit,
            "start": (self._page - 1) * self._limit if self._page > 0 else 0,
            "organizationId": config.get("landong", "organization_id"),
        }
        return data

    def get_api_route(self):
        return self.PATH

    def get_unique_define(self):
        return ":".join([self.PATH, str(self._page), str(Date().now().timestamp())])

    def parse_response(self, response, task):
        content = response.json
        data = content.get("data", [])
        total = content.get("total", 0)

        # 新款档案如果有新增或者更新，就通知给天鸽, 顺便更新到es
        self.inform_to_tg(data)

        # 抓取下一页
        if self.next_page and total > self._limit * self._page:
            self.crawl_handler_page(PatternDesign(self.next_page).set_page(self._page + 1))

        # 解析响应
        return {
            "response": response.text[:200]
        }

    def inform_to_tg(self, data):
        """
        新款档案 如果有新增或者更新，就通知给天鸽
        :param data:
        """
        # 保存到es的数据
        save_to_es_data = []
        # 把数据保存到内存
        origin_patter_design_map = {}
        # 发送给天鸽的数据
        tg_patter_design_list = []
        all_patter_designs = PatternDesignEs().get_all_pattern_design()
        for patter_design_list in all_patter_designs:
            for bas in patter_design_list:
                origin_patter_design_map.setdefault(bas.get("UUID", "none-1"), bas)

        # 判断数据是否是新增或更新的
        for item in data:
            uuid = item.get("UUID", "")
            update_time = item.get("UpdateOn")

            origin_bas_brand = origin_patter_design_map.get(uuid)
            if origin_bas_brand is None:
                # 新增
                tg_patter_design_list.append(self.build_post_data(item))
                save_to_es_data.append(item)
            else:
                # 更新
                origin_update_time = origin_bas_brand.get("UpdateOn")
                if update_time:
                    if "." in update_time:
                        update_time = update_time.split(".", 1)[0]
                    if not origin_update_time:
                        tg_patter_design_list.append(self.build_post_data(item))
                        save_to_es_data.append(item)
                    else:
                        if "." in origin_update_time:
                            origin_update_time = origin_update_time.split(".", 1)[0]
                        if Date(update_time) > Date(origin_update_time):
                            tg_patter_design_list.append(self.build_post_data(item))
                            save_to_es_data.append(item)

        for post_data in tg_patter_design_list:
            # 新款档案的详情图也需要抓取 - 图稿标签里最新图稿的商品图片
            self.crawl_handler_page(
                PatternDesignImageItemId(post_data).set_priority(PatternDesignImageItemId.CONST_PRIORITY_FIRST))

        # 有更新的数据才更新到es
        sync_time = Date.now().format_es_utc_with_tz()
        for item in save_to_es_data:
            item["sync_time"] = sync_time
        PatternDesignEs().update(save_to_es_data, async=True)

    def build_post_data(self, item: dict):
        """
        构造发送给天鸽的数据
        :param item:
        :return:
        """
        uuid = item.get("UUID", "")  # 唯一key
        # 商品主图
        store_name = item.get("StoreName", "")
        if store_name:
            img_url = "https://v3.ldyerp.com/Plm/ArtWork/Thumb?name={}&width=500&height=500".format(store_name)
            # 图片上传到oss
            oss_img_path = oss_cdn.get_key(oss_cdn.CONST_LANDONG_IMAGE, store_name)
            self.crawl_handler_page(ImageDownload(img_url, oss_img_path, self.get_cookie()))
            imgs = ["https://{bucket_name}.{endpoint}/{oss_img_path}".format(
                bucket_name=config.get("oss_cdn", "bucket_name"),
                endpoint=config.get("oss_cdn", "endpoint"),
                oss_img_path=oss_img_path).replace("\\", "%5C").replace("-internal", "")]
        else:
            imgs = []
        design_code = item.get("DesignCode", "")  # 设计款号
        band_name = item.get("BandName", "")  # 波段名字
        band_item = BasBrandEs().get_band_item_by_name(band_name)
        band_code = band_item.get("DataCode", "") if band_item else ""  # 波段编码
        name = item.get("PatternName", "")  # 商品名称
        year = item.get("Year", 0)  # 年份
        season = item.get("SeasonName", "")  # 季节
        unit_id = unit_map.get(item.get("UnitName", ""), 0)  # 单位 Id
        brand_id = brand_map.get(item.get("BrandName", ""), 0)  # 品牌Id
        design_source_id = design_source_map.get(item.get("PatternPropertyName", ""), 0)  # 设计来源Id
        category_item = BasProductCategoryEs().get_category_by_name(item.get("ProductCategoryName", ""))
        category_code = category_item.get("CategoryCode", "") if category_item else ""  # 类目code
        input_designer_name = item.get("UseAgeName", "")  # 设计师名字 - 对应澜东云的使用年龄字段
        designer_name = item.get("DesignerName", "")  # 产品经理 - 对应澜东云设计师字段
        buyer = designer_name  # 买手-plm的产品经理
        creator = item.get("CreateByName", "")  # 创建人
        is_suit_item = item.get("GenderName", "").strip()  # 是否套装, 0:无数据, 1:套装, 2: 非套装 - 对应澜东云性别字段
        if is_suit_item == "非套装":
            is_suit = 2
        elif is_suit_item == "套装":
            is_suit = 1
        else:
            is_suit = 0
        return {
            "imgs": imgs,
            "designCode": design_code,
            "bandCode": band_code,
            "name": name,
            "year": year,
            "season": season,
            "unitId": unit_id,
            "brandId": brand_id,
            "designSourceId": design_source_id,
            "categoryCode": category_code,
            "designerName": input_designer_name,
            "buyer": buyer,
            "uuid": uuid,
            "creator": creator,
            "isSuit": is_suit,
        }

    def get_user_id_by_name(self, designer_name):
        """
        根据员工名字获取员工ID
        :param designer_name:
        :return:
        """
        return PlmAdminId(designer_name).get_result().get("result", {}).get("data", {}).get("id", 0)

from landong.model.es.mass_pattern_design import MassPatternDesignEs
from landong.page.base import Base
from landong.page.inform.plm_mass_pattern_design import PlmMassPatternDesignInform
from landong.page.plm_mass_pattern_design_color_size_list import MassPatternDesignColorSizeList
from pyspider.helper.date import Date
from pyspider.config import config


class MassPatternDesign(Base):
    """
    商品档案
    """

    PATH = "/Plm/MassPatternDesign/PagedQuery"

    def __init__(self, next_page=False):
        super(MassPatternDesign, self).__init__()
        self.next_page = next_page

    def get_api_route(self):
        return self.PATH

    def get_unique_define(self):
        return ":".join([self.PATH, str(self._page), str(Date().now().timestamp())])

    def get_post_data(self):
        return {
            "filter": "",
            "organizationId": config.get("landong", "organization_id"),
            "page": self._page,
            "start": (self._page - 1) * self._limit if self._page > 0 else 0,
            "limit": self._limit,
        }

    def parse_response(self, response, task):
        content = response.json
        total = content.get("total", 0)
        data = content.get("data", [])

        # 商品档案如果有新增或者更新，就通知给天鸽
        self.inform_to_tg(data)

        sync_time = Date.now().format_es_utc_with_tz()
        for _ in data:
            self.crawl_handler_page(
                MassPatternDesignColorSizeList(uuid=_.get("UUID"), design_code=_.get("DesignCode"),
                                               mass_code=_.get("MassCode")).set_crawl_host("page_host"))
            _["sync_time"] = sync_time
        MassPatternDesignEs().update(data, async=True)

        # 爬取下一页
        if self.next_page and total > self._page * self._limit:
            self.crawl_handler_page(MassPatternDesign(self.next_page).set_page(self._page + 1))

        # 返回响应结果
        return {
            "response": response.text[:200],
            "sync_time": sync_time,
        }

    def inform_to_tg(self, data):
        """
        若有更新或者变动通知tg
        """
        shop_data_list = []
        shop_data = MassPatternDesignEs().get_all_pattern_design()

        # 判断商品档案是否有更新
        for item in data:
            uuid = item.get("UUID", "")
            spu_barcode = item.get("MassCode", "")
            design_code = item.get("DesignCode", "")
            update_time = item.get("UpdateOn")
            shop_map = {
                "spuBarcode": spu_barcode,
                "designCode": design_code
            }

            shop = shop_data.get(uuid)

            if shop is None:
                # 新增
                shop_data_list.append(shop_map)
            else:
                # 更新
                shop_update_time = shop.get("UpdateOn")
                if update_time:
                    if "." in update_time:
                        update_time = update_time.split(".")[0]
                    if not shop_update_time:
                        shop_data_list.append(shop_map)
                    else:
                        if "." in shop_update_time:
                            shop_update_time = shop_update_time.split(".")[0]
                        if Date(update_time) > Date(shop_update_time):
                            shop_data_list.append(shop_map)
        if len(shop_data_list) > 0:
            self.crawl_handler_page(PlmMassPatternDesignInform(data=shop_data_list))

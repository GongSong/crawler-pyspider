from landong.model.es.mass_pattern_design_color_size import MassPatternDesignColorSizeEs
from landong.page.base import Base
from landong.page.inform.plm_mass_pattern_design_color_size import PlmMassPatternDesignColorSizeInform
from pyspider.helper.date import Date


class MassPatternDesignColorSizeList(Base):
    """
    商品档案-商品编码
    """

    PATH = "/Plm/MassPatternDesignColorSizeList/GetMassPatternDesignColorSizeList?massPatternDesignId="

    def __init__(self, uuid=None, design_code=None, mass_code=None):
        super(MassPatternDesignColorSizeList, self).__init__()
        self.uuid = uuid
        self.design_code = design_code
        self.mass_code = mass_code

    def get_api_route(self):
        return self.PATH + self.uuid

    def get_unique_define(self):
        return self.uuid

    def get_post_data(self):
        return {
            "filter": "",
            "page": self._page,
            "start": (self._page - 1) * self._limit if self._page > 0 else 0,
            "limit": self._limit,
        }

    def parse_response(self, response, task):
        content = response.json
        data = content.get("data", [])

        self.inform_to_tg(data)

        sync_time = Date.now().format_es_utc_with_tz()
        for _ in data:
            # 软删除标志位, 爬虫没爬到就当做被删除了
            # deleted: True:已删除, False:未删除
            _["deleted"] = False
            _["sync_time"] = sync_time
        MassPatternDesignColorSizeEs().update(data, async=True)

        # 返回响应结果
        return {
            "response": response.text[:200],
            "sync_time": sync_time
        }

    def inform_to_tg(self, data):
        """
        这里面涉及澜东云的sku数据
        若有更新或者变动通知tg
        如果sku没有同步到tg，可能是因为数据已经爬到es了，所以没有通知，解决方式就是删掉es里的相关sku数据，再重新爬一遍即可
        """
        sku_data_list = []
        new_sku_list = []
        for item in data:
            if item.get("SKU"):
                new_sku_list.append(item.get("SKU"))

        sku_list, sku_map = MassPatternDesignColorSizeEs().mass_code_get_sku(self.mass_code)

        if sorted(new_sku_list) != sorted(sku_list):
            for item in data:
                color_code = item.get("ColorCode", "")
                size_code = item.get("SizeCode", "")
                sku = item.get("SKU", "")
                skc = item.get("SKC", "")
                sku_data_list.append(
                    {
                        "baseColorCode": color_code[:1],
                        "subColorCode": int(color_code[1:]),
                        "sizeCode": size_code,
                        "skuBarcode": sku,
                        "skcBarcode": skc,
                    })

            # 没爬到的商品标记为已删除
            delete_sku_list = []
            sync_time = Date.now().format_es_utc_with_tz()
            for sku in sku_list:
                if sku not in new_sku_list:
                    delete_item = sku_map.get(sku, {})
                    delete_item["deleted"] = True
                    delete_item["sync_time"] = sync_time
                    delete_sku_list.append(delete_item)
            if len(delete_sku_list) > 0:
                MassPatternDesignColorSizeEs().update(delete_sku_list, async=True)

            if len(sku_data_list) > 0:
                self.crawl_handler_page(
                    PlmMassPatternDesignColorSizeInform(design_code=self.design_code, data=sku_data_list))

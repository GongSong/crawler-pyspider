from landong.model.es.bas_product_color import BasProductColorEs
from landong.page.base import Base
from landong.page.corn.corn import send_ding_talk
from landong.page.inform.pattern_design import PatternDesignInform
from pyspider.helper.date import Date


class PatternDesignColors(Base):
    """
    新款档案详情的颜色列表 - 获取 属性 标签里的颜色列表信息
    """

    PATH = "/Plm/PatternDesignProp/GetPatternDesignColorList"

    def __init__(self, design_id, post_data: dict, size_list: list):
        super(PatternDesignColors, self).__init__()
        self.post_data = post_data
        self.size_list = size_list
        self.design_id = design_id

    def get_post_data(self):
        data = {
            "page": self._page,
            "limit": self._limit,
            "start": (self._page - 1) * self._limit if self._page > 0 else 0,
        }
        return data

    def get_api_route(self):
        return self.PATH + "?designId={}".format(self.design_id)

    def get_unique_define(self):
        return ":".join([self.PATH, str(self.design_id), self.post_data.get("uuid", "")])

    def parse_response(self, response, task):
        content = response.json
        data = content.get("data", [])

        # 获取颜色列表
        color_list = [item.get("ColorName", "") for item in data]
        colors = []
        color_item_list = BasProductColorEs().get_bas_color_by_names(color_list) if color_list else []

        # 如果查询到的尺码之前没有被爬虫爬到，则认定为异常数据，钉钉报警并且不调用天鸽的数据更新接口
        if len(color_list) != len(color_item_list):
            self.send_warning_msg(color_item_list, color_list)
            return {
                "err_msg": "颜色之前没有被爬虫爬到，被认定为异常数据，钉钉报警并且不调用天鸽的数据更新接口",
                "response": response.text[:200],
                "color_list": color_list,
            }

        for color in color_item_list:
            color_code = color.get("ColorCode", "")
            color_name = color.get("ColorName", "")
            colors.append({
                "baseCode": color_code[:1] if color_code else "",  # 颜色Code首字母
                "subCode": int(color_code[1:]) if color_code else "",  # 颜色Code第二个字母
                "sizeIds": self.size_list,  # 尺码Id列表
                "colorName": color_name,  # 颜色名称
            })
        self.post_data["colors"] = colors

        # 通知给天鸽
        self.crawl_handler_page(PatternDesignInform(self.post_data))

        # 解析响应
        return {
            "response": response.text[:200],
            "colors": colors
        }

    def send_warning_msg(self, color_item_list, color_list):
        """
        发送报警
        :param color_item_list:
        :param color_list:
        :return:
        """
        error_name_list = []
        es_name_str_list = [item.get("ColorName", "") for item in color_item_list]
        for item in color_list:
            if item not in es_name_str_list:
                error_name_list.append(item)

        if error_name_list:
            error_name_str = ":".join(error_name_list)
            title = "澜东云-新款档案详情 的 颜色列表: 部分颜色异常"
            text = "设计款号:{} 的颜色:{} 有异常".format(self.post_data.get("designCode", ""), error_name_str)
            send_ding_talk(title, text, self.post_data.get("designCode", "") + error_name_str)

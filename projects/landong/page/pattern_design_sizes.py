from landong.model.es.bas_pattern_size import BasPatternSizeEs
from landong.page.base import Base
from landong.page.corn.corn import send_ding_talk
from landong.page.pattern_design_colors import PatternDesignColors
from pyspider.helper.date import Date


class PatternDesignSizes(Base):
    """
    新款档案详情的尺码列表 - 获取 属性 标签里的尺码列表信息
    """

    PATH = "/Plm/PatternDesignProp/GetPatternDesignSizeList"

    def __init__(self, design_id, post_data: dict):
        super(PatternDesignSizes, self).__init__()
        self.post_data = post_data
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

        # 获取尺码列表
        size_name_list = [item.get("SizeName", "") for item in data]
        size_list = []
        if size_name_list:
            es_name_list = BasPatternSizeEs().get_size_by_name(size_name_list)
            # 如果查询到的尺码之前没有被爬虫爬到，则认定为异常数据，钉钉报警并且不调用天鸽的数据更新接口
            if len(es_name_list) != len(size_name_list):
                self.send_warning_msg(es_name_list, size_name_list)
                return {
                    "err_msg": "尺码之前没有被爬虫爬到，被认定为异常数据，钉钉报警并且不调用天鸽的数据更新接口",
                    "response": response.text[:200],
                    "size_name_list": size_name_list,
                }

            for item in es_name_list:
                size_list.append(item.get("DataCode", ""))

        # 获取颜色列表
        self.crawl_handler_page(PatternDesignColors(self.design_id, self.post_data, size_list))

        # 解析响应
        return {
            "response": response.text[:200],
            "size_list": size_list
        }

    def send_warning_msg(self, es_name_list, size_name_list):
        """
        发送报警
        :param es_name_list:
        :param size_name_list:
        :return:
        """
        error_name_list = []
        es_name_str_list = [item.get("DataName", "") for item in es_name_list]
        for item in size_name_list:
            if item not in es_name_str_list:
                error_name_list.append(item)

        if error_name_list:
            error_name_str = ":".join(error_name_list)
            title = "澜东云-新款档案详情的尺码列表: 部分尺码异常"
            text = "设计款号:{} 的尺码:{} 有异常".format(self.post_data.get("designCode", ""), error_name_str)
            send_ding_talk(title, text, self.post_data.get("designCode", "") + error_name_str)

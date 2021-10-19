import uuid
from copy import deepcopy

from hupun.page.base import *
from hupun.page.hupun_goods.goods_information_sku import GoodsInformationsku


class GoodsInfoEnble(Base):
    """
    根据「商品规格」在「万里牛商品信息」里「开启」商品数据;
    同步「开启」，返回结果;
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
  "action": "resolve-data",
  "dataResolver": "goodsInterceptor#saveGoods",
  "dataItems": [
    {
      "alias": "dsGoods",
      "data": {
        "$isWrapper": true,
        "$dataType": "v:goods.Goods$[Goods]",
        "data": %s
      },
      "refreshMode": "value",
      "autoResetEntityState": true
    }
  ],
  "parameter": {
    "oper": "modify",
    "enable": "0"
  },
  "context": {}
 }
]]></request>
</batch>
"""

    def __init__(self, enable_data):
        """
        同步「开启」商品信息
        :param enable_data: 启用商品的构造接口信息
        """
        super(GoodsInfoEnble, self).__init__()
        self.__enable_data = deepcopy(enable_data)

    def get_request_data(self):
        return self.request_data % json.dumps(self.__enable_data)

    def get_unique_define(self):
        return merge_str('goods_info_enable', uuid.uuid4())

    def parse_response(self, response, task):
        # json 结果
        result = self.detect_xml_text(response.text)
        return result

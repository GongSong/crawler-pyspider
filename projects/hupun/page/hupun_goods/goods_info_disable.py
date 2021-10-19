import uuid
from copy import deepcopy

from hupun.page.base import *
from hupun.page.hupun_goods.goods_information_sku import GoodsInformationsku


class GoodsInfoDisable(Base):
    """
    根据「商品规格」在「万里牛商品信息」里「关闭」商品数据;
    同步「关闭」，返回结果;
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
    "enable": "1"
  },
  "context": {}
 }
]]></request>
</batch>
"""

    def __init__(self, close_data):
        """
        同步「关闭」商品信息
        :param close_data: 关闭商品的构造接口信息
        """
        super(GoodsInfoDisable, self).__init__()
        self.__close_data = deepcopy(close_data)

    def get_request_data(self):
        return self.request_data % json.dumps(self.__close_data)

    def get_unique_define(self):
        return merge_str('goods_info_disable', uuid.uuid4())

    def parse_response(self, response, task):
        # json 结果
        result = self.detect_xml_text(response.text)
        return result

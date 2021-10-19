import uuid

from hupun.page.base import *


class OrSkuRename(Base):
    """
    在订单审核页面根据订单号更改对应的商品sku
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
  "action": "resolve-data",
  "dataResolver": "saleInterceptor#saveOrder",
  "dataItems": [
    {
      "alias": "trade",
      "data": {
        "$isWrapper": true,
        "$dataType": "v:sale.approve$[Trade]",
        "data": %s
      },
      "refreshMode": "value",
      "autoResetEntityState": true
    },
    {
      "alias": "order",
      "data": {
        "$isWrapper": true,
        "$dataType": "v:sale.approve$[Order]",
        "data": %s
      },
      "refreshMode": "value",
      "autoResetEntityState": true
    }
  ],
  "parameter": {
    "type": 1
  },
  "context": {}
 }
]]></request>
</batch>
"""

    def __init__(self, first_data, second_data):
        super(OrSkuRename, self).__init__()
        self.__first_data = first_data
        self.__second_data = second_data

    def get_request_data(self):
        req_data = self.request_data % (json.dumps(self.__first_data), json.dumps(self.__second_data))
        return req_data

    def get_unique_define(self):
        return merge_str('order_sku_rename', uuid.uuid4())

    def parse_response(self, response, task):
        # json 结果
        result = self.detect_xml_text(response.text)
        return result

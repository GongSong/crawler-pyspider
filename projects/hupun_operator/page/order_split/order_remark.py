import uuid
from copy import deepcopy

from hupun.page.base import *


class OrderRemark(Base):
    """
    在订单审核页面根据订单号查询需要拆分的订单
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
  "action": "resolve-data",
  "dataResolver": "saleInterceptor#saveTrade",
  "dataItems": [
    {
      "alias": "dsTrade",
      "data": {
        "$isWrapper": true,
        "$dataType": "Trade",
        "data": [
          %s
        ]
      },
      "refreshMode": "value",
      "autoResetEntityState": true
    }
  ],
  "parameter": {
    "type": 8,
    "property": "remark",
    "view": "sale.approve",
    "oldValue": "%s",
    "newValue": "%s"
  },
  "context": {}
}
]]></request>
</batch>
"""

    def __init__(self, remark_data, old_remark, new_remark):
        super(OrderRemark, self).__init__()
        self.__remark_data = deepcopy(remark_data)
        self.__old_remark = old_remark
        self.__new_remark = new_remark

    def get_request_data(self):
        req_data = self.request_data % (json.dumps(self.__remark_data), self.__old_remark, self.__new_remark)
        return req_data

    def get_unique_define(self):
        return merge_str('order_remark', uuid.uuid4())

    def parse_response(self, response, task):
        # json 结果
        result = self.detect_xml_text(response.text)
        return result

import uuid
from copy import deepcopy

from hupun.page.base import *


class SubmitPurBillStock(Base):
    """
    提交 采购入库单 的采购订单入库申请
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
  "action": "remote-service",
  "service": "stockBillInterceptor#checkGoodsSpec",
  "supportsEntity": true,
  "parameter": {
    "details": {
      "$isWrapper": true,
      "$dataType": "v:purchase.stock$[dtStockBillDetail]",
      "data": %s
    }
  },
  "context": {},
  "loadedDataTypes": [
    "GoodsSpec",
    "PrintConfig",
    "dtSearchGoods",
    "FinAccount",
    "MultiOper",
    "dtResult",
    "dtStockBillDetail",
    "Combination",
    "dtBatchInventory",
    "locInventory",
    "Oper",
    "dtSearch",
    "Template",
    "Storage",
    "dtStcockBill",
    "Currency",
    "dtFractUnit",
    "Catagory",
    "GoodsPermissions",
    "CombinationDetail",
    "dtSerialNumber"
  ]
}
]]></request>
</batch>
"""

    def __init__(self, data):
        super(SubmitPurBillStock, self).__init__()
        self.__data = deepcopy(data)

    def get_request_data(self):
        req_data = self.request_data % json.dumps(self.__data)
        return req_data

    def get_unique_define(self):
        return merge_str('submit_purchase_bill_stock', uuid.uuid4())

    def parse_response(self, response, task):
        # json 结果
        result = self.detect_xml_text(response.text)['data']
        return result

import uuid

from hupun.page.base import *


class PurchaseStockToken(Base):
    """
    获取 采购入库单 的采购订单入库申请时的 Token
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
   "action":"remote-service",
   "service":"mainService#getRequestToken",
   "supportsEntity":true,
   "context":{},
   "loadedDataTypes":[
     "Storage",
     "dtStockBillDetail",
     "Oper",
     "dtBatchInventory",
     "dtStcockBill",
     "Combination",
     "Catagory",
     "dtSearchGoods",
     "MultiOper",
     "Template",
     "PrintConfig",
     "GoodsSpec",
     "dtFractUnit",
     "dtSearch",
     "locInventory",
     "FinAccount",
     "dtResult",
     "Currency",
     "CombinationDetail",
     "GoodsPermissions",
     "dtSerialNumber"
   ]
 }
]]></request>
</batch>
"""

    def __init__(self):
        super(PurchaseStockToken, self).__init__()

    def get_request_data(self):
        return self.request_data

    def get_unique_define(self):
        return merge_str('get_purchase_bill_stock_token', uuid.uuid4())

    def parse_response(self, response, task):
        # json 结果
        result = self.detect_xml_text(response.text)['data']
        return result

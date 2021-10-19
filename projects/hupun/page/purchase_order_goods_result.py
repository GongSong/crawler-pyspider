from hupun.page.base import *


class PurOrderGoodsResult(Base):
    """
    采购订单商品详情 的数据
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
   "action":"load-data",
   "dataProvider":"purchaseInterceptor#queryPurchaseDetail",
   "supportsEntity":true,
   "parameter":"%s",
   "resultDataType":"v:purchase.bill$[pchs_detail]",
   "context":{},
   "loadedDataTypes":[
     "Template",
     "replenishBill",
     "Oper",
     "pchs_detail",
     "pchs_bill_log",
     "purchaseBill",
     "pchsInfo",
     "dtCondition",
     "Currency",
     "dtConditionGoods",
     "Supplier",
     "pcshBillBImport",
     "Region",
     "PrintConfig",
     "Storage",
     "dtSearch",
     "dtPurchaseStream",
     "dtStatus",
     "dtPchsGoods",
     "Catagory",
     "dtFractUnit",
     "MultiOper",
     "GoodsSpec",
     "dtException",
     "replenishInfo",
     "dtPostiveNum",
     "GoodsPermissions"
   ]
 }
]]></request>
</batch>
"""

    def __init__(self, bill_uid):
        super(PurOrderGoodsResult, self).__init__()
        self.__bill_uid = bill_uid

    def get_request_data(self):
        return self.request_data % self.__bill_uid

    def get_unique_define(self):
        return merge_str('purchase_order_goods_result', self.__bill_uid)

    def parse_response(self, response, task):
        # json 结果
        result = self.detect_xml_text(response.text)
        return result['data']

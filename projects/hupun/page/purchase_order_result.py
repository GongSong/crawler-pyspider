from hupun.page.base import *


class PurchaseOrderResult(Base):
    """
    采购订单 的直接返回数据
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
   "action":"load-data",
   "dataProvider":"purchaseInterceptor#queryBill",
   "supportsEntity":true,
   "parameter":{
     "billType":0,
     "days":"30",
     "startDate":"%s",
     "endDate":"%s",
     "view":"purchase.bill",
     "salemanUids":"",
     "saleman":"",
     "billCode":"%s",
     "his":false
   },
   "resultDataType":"v:purchase.bill$[purchaseBill]",
   "pageSize":"%d",
   "pageNo":%d,
   "context":{},
   "loadedDataTypes":[
     "replenishBill",
     "purchaseBill",
     "pchs_bill_log",
     "Region",
     "dtCondition",
     "Catagory",
     "pchs_detail",
     "Template",
     "dtFractUnit",
     "MultiOper",
     "Currency",
     "pcshBillBImport",
     "pchsInfo",
     "dtPurchaseStream",
     "GoodsSpec",
     "dtPostiveNum",
     "PrintConfig",
     "Storage",
     "Oper",
     "dtStatus",
     "Supplier",
     "dtConditionGoods",
     "dtException",
     "dtSearch",
     "replenishInfo",
     "dtPchsGoods",
     "GoodsPermissions"
   ]
 }
]]></request>
</batch>
"""

    def __init__(self, bill_code):
        super(PurchaseOrderResult, self).__init__()
        self.__bill_code = bill_code

    def get_request_data(self):
        start_date = Date(self._start_time).format_es_old_utc() if self._start_time else \
            Date.now().format_es_old_utc()
        end_date = Date(self._end_time).format_es_old_utc() if self._end_time else \
            Date.now().format_es_old_utc()
        return self.request_data % (start_date, end_date, self.__bill_code, self._page_size, self._page)

    def get_unique_define(self):
        return merge_str('purchase_order_result', self._page, self._page_size, self._start_time, self._end_time)

    def parse_response(self, response, task):
        # json 结果
        result = self.detect_xml_text(response.text)
        return_result = result['data']['data']
        return return_result[0]

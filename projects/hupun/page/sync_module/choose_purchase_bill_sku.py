from hupun.page.base import *


class ChoosePurBillSku(Base):
    """
    根据 bill_uid 获取 采购入库单 的采购订单下的商品详情
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
   "action":"load-data",
   "dataProvider":"purchaseInterceptor#queryDetail4StockIn",
   "supportsEntity":true,
   "parameter":{
     "billUid":"%s",
     "detail_uid":"",
     "multiStatus":"0,1",
     "receiveGTzero":false,
     "goods":null
   },
   "sysParameter":{},
   "resultDataType":"v:purchase.SelectPchsBill$[pchsBill]",
   "context":{},
   "loadedDataTypes":[
     "dtSearchGoods",
     "dtCondition",
     "Storage",
     "pchsBill"
   ]
 }
]]></request>
</batch>
"""

    def __init__(self, bill_uid):
        super(ChoosePurBillSku, self).__init__()
        self.__bill_uid = bill_uid

    def get_request_data(self):
        return self.request_data % self.__bill_uid

    def get_unique_define(self):
        return merge_str('choose_purchase_bill_sku', self.__bill_uid)

    def parse_response(self, response, task):
        # json 结果
        result = self.detect_xml_text(response.text)['data']
        return result

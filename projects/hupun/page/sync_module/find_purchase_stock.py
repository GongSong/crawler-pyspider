import uuid

from hupun.page.base import *


class FindPurStock(Base):
    """
    根据供应商, 仓库和商品编码等参数获取 新生成的 采购入库单 的单据编号
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
   "action":"load-data",
   "dataProvider":"stockBillInterceptor#searchStockBill",
   "supportsEntity":true,
   "parameter":{
     "days":"0",
     "startDate":"%s",
     "endDate":"%s",
     "view":"purchase.stock",
     "his":false,
     "needTemplate":true,
     "payment":0,
     "billType":6,
     "salemanUids":"",
     "saleman":"",
     "supplierId":"%s",
     "supplierName":"%s",
     "storage_uid":"%s",
     "storage_name":"%s",
     "specCode":null,
     "goods":null,
     "$dataType":"v:purchase.stock$dtSearch"
   },
   "resultDataType":"v:purchase.stock$[dtStcockBill]",
   "pageSize":20,
   "pageNo":1,
   "context":{},
   "loadedDataTypes":[
    "dtSearchGoods",
    "Currency",
    "Catagory",
    "Template",
    "dtStockBillDetail",
    "dtSearch",
    "FinAccount",
    "dtBatchInventory",
    "Combination",
    "GoodsSpec",
    "Oper",
    "MultiOper",
    "dtStcockBill",
    "Storage",
    "PrintConfig",
    "dtResult",
    "locInventory",
    "dtFractUnit",
    "CombinationDetail",
    "dtSerialNumber",
    "GoodsPermissions"
  ]
 }
]]></request>
</batch>
"""

    def __init__(self, storage_uid, storage_name, supplier_uid, supplier_name):
        super(FindPurStock, self).__init__()
        self.__storage_uid = storage_uid
        self.__storage_name = storage_name
        self.__supplier_uid = supplier_uid
        self.__supplier_name = supplier_name

    def get_request_data(self):
        start_date = Date(self._start_time).to_day_start().format_es_old_utc() if self._start_time else \
            Date.now().to_day_start().format_es_old_utc()
        end_date = Date(self._end_time).format_es_old_utc() if self._end_time else \
            Date.now().format_es_old_utc()
        return self.request_data % (
            start_date, end_date, self.__supplier_uid, self.__supplier_name, self.__storage_uid, self.__storage_name)

    def get_unique_define(self):
        return merge_str('find_purchase_stock', uuid.uuid4())

    def parse_response(self, response, task):
        # json 结果
        result = self.detect_xml_text(response.text)['data']['data']
        return result

from hupun.page.base import *
from hupun.model.es.purchase_store_order_goods import PurchaseStoreOrderGoods as EsPurchaseOrderGoods


class PurchaseStoreOrderGoods(Base):
    """
    采购入库单 的 查看详情数据
    """
    request_data = """
<batch>
<request type="json">
<![CDATA[
 {
   "action":"load-data",
   "dataProvider":"stockBillInterceptor#getStockBillDetailList",
   "supportsEntity":true,
   "parameter":{
     "stockId":"%s"
   },
   "resultDataType":"v:stock.stockBill$[StockBillDetail]",
   "pageSize":0,
   "pageNo":1,
   "context":{},
   "loadedDataTypes":[
     "StockBill",
     "StockBillDetail",
     "dtBatch",
     "dtSerialNumber",
     "dtStcockBill",
     "Oper",
     "dtStockBillDetail",
     "PrintConfig",
     "GoodsSpec",
     "Template",
     "dtSearch",
     "Storage",
     "locInventory",
     "Catagory",
     "dtFractUnit",
     "dtSearchGoods",
     "MultiOper",
     "Currency",
     "dtBatchInventory",
     "FinAccount",
     "dtResult",
     "GoodsPermissions"
   ]
}]]></request>
</batch>
"""

    def __init__(self, stock_uid):
        super(PurchaseStoreOrderGoods, self).__init__()
        self.__stock_uid = stock_uid

    def get_request_data(self):
        return self.request_data % self.__stock_uid

    def get_unique_define(self):
        return merge_str(
            'purchase_store_order_goods',
            self.__stock_uid,
        )

    def parse_response(self, response, task):
        # 爬虫的抓取时间
        sync_time = Date.now().format_es_utc_with_tz()
        # json 结果
        result = self.detect_xml_text(response.text)
        if len(result['data']):
            for _item in result['data']:
                _item['sync_time'] = sync_time
                self.send_message(_item, merge_str('purchase_store_order_goods', _item.get('stock_detail_uid', '')))
            EsPurchaseOrderGoods().update(result['data'], async=True)
        return {
            # 'text': response.text,
            'stock_uid': self.__stock_uid,
        }

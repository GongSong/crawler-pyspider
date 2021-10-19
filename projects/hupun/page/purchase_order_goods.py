from hupun.page.base import *
from hupun.model.es.purchase_order_goods import PurchaseOrderGoods as POrderGoodsEs


class PurchaseOrderGoods(Base):
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
        super(PurchaseOrderGoods, self).__init__()
        self.__bill_uid = bill_uid

    def get_request_data(self):
        return self.request_data % self.__bill_uid

    def get_unique_define(self):
        return merge_str('purchase_order_goods', self.__bill_uid)

    def parse_response(self, response, task):
        # 爬虫的抓取时间
        sync_time = Date.now().format_es_utc_with_tz()
        # json 结果
        result = self.detect_xml_text(response.text)
        if len(result['data']):
            for _item in result['data']:
                _item['sync_time'] = sync_time
                self.send_message(_item, merge_str('purchase_order_goods', _item.get('detail_uid', '')))
            # 这个异步更新数据需要开启 es 队列去消费
            POrderGoodsEs().update(result['data'], async=True)
        return {
            'tag': '采购订单查看详情的数据',
            # 'text': response.text,
            'page': self._page,
        }

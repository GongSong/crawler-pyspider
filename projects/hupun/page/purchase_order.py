from hupun.page.base import *
from hupun.model.es.purchase_order import PurchaseOrder as POrderEs
from hupun.page.purchase_order_goods import PurchaseOrderGoods


class PurchaseOrder(Base):
    """
    采购订单 的数据
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
     "days":null,
     "startDate":"%s",
     "endDate":"%s",
     "view":"purchase.bill",
     "salemanUids":"",
     "saleman":"",
     "his":false
   },
   "resultDataType":"v:purchase.bill$[purchaseBill]",
   "pageSize":%d,
   "pageNo":%d,
   "context":{},
   "loadedDataTypes":[
     "pchsInfo",
     "pchs_detail",
     "dtCondition",
     "dtStatus",
     "pcshBillBImport",
     "Region",
     "MultiOper",
     "GoodsSpec",
     "dtPostiveNum",
     "dtPchsGoods",
     "replenishInfo",
     "pchs_bill_log",
     "dtSearch",
     "dtPurchaseStream",
     "purchaseBill",
     "Supplier",
     "Storage",
     "replenishBill",
     "Currency",
     "dtFractUnit",
     "Oper",
     "dtConditionGoods",
     "dtException",
     "Catagory",
     "Template",
     "PrintConfig",
     "GoodsPermissions"
   ]
 }
]]></request>
</batch>
"""

    def __init__(self, go_next_page=False):
        super(PurchaseOrder, self).__init__()
        self.__go_next_page = go_next_page

    def get_request_data(self):
        start_date = Date(self._start_time).to_day_start().format_es_old_utc() if self._start_time else \
            Date.now().to_day_start().format_es_old_utc()
        end_date = Date(self._end_time).format_es_old_utc() if self._end_time else \
            Date.now().format_es_old_utc()
        return self.request_data % (start_date, end_date, self._page_size, self._page)

    def get_unique_define(self):
        return merge_str('purchase_order', self._page, self._page_size, self._start_time, self._end_time)

    def parse_response(self, response, task):
        # 爬虫的抓取时间
        sync_time = Date.now().format_es_utc_with_tz()
        # json 结果
        result = self.detect_xml_text(response.text)
        if len(result['data']['data']):
            for _item in result['data']['data']:
                _item['sync_time'] = sync_time
                # 抓取采购订单的查看详情数据
                self.crawl_handler_page(
                    PurchaseOrderGoods(_item['bill_uid']).set_cookie_position(self._cookies_position))
                self.send_message(_item, merge_str('purchase_order', _item.get('bill_uid', '')))
            # 这个异步更新数据需要开启 es 队列去消费
            POrderEs().update(result['data']['data'], async=True)
            # 抓取下一页
            self.crawl_next_page()
        return {
            'tag': '采购订单的数据',
            # 'text': response.text,
            'page': self._page,
        }

    def crawl_next_page(self):
        """
        爬下一页
        :return:
        """
        if self.__go_next_page and not self.check_flag(self.CONST_FLAG_BREAK) and self.in_processor():
            self.crawl_handler_page(
                PurchaseOrder(go_next_page=self.__go_next_page)
                    .set_page(self._page + 1)
                    .set_page_size(self._page_size)
                    .set_start_time(self._start_time)
                    .set_end_time(self._end_time)
                    .set_priority(self._priority)
                    .set_cookie_position(self._cookies_position)
            )

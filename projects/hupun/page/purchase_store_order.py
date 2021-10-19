from hupun.page.base import *
from hupun.model.es.purchase_store_order import PurchaseStoreOrder as EsPurchaseOrder
from hupun.page.purchase_store_order_goods import PurchaseStoreOrderGoods


class PurchaseStoreOrder(Base):
    """
    采购入库单 的 面板数据
    """
    request_data = """
<batch>
<request type="json">
<![CDATA[
 {
   "action":"load-data",
   "dataProvider":"stockBillInterceptor#searchStockBill",
   "supportsEntity":true,
   "parameter":{
     "days":"%d",
     "startDate":"%s",
     "endDate":"%s",
     "view":"purchase.stock",
     "his":%s,
     "needTemplate":true,
     "payment":0,
     "billType":6,
     "salemanUids":"",
     "saleman":"",
     "$dataType":"v:purchase.stock$dtSearch"
    },
    "resultDataType":"v:purchase.stock$[dtStcockBill]",
    "pageSize":"%d",
    "pageNo":%d,
    "context":{},
    "loadedDataTypes":[
     "GoodsSpec",
    "dtResult",
    "PrintConfig",
    "MultiOper",
    "FinAccount",
    "locInventory",
    "Storage",
    "Template",
    "Currency",
    "dtBatchInventory",
    "Catagory",
    "Combination",
    "Oper",
    "dtSearch",
    "dtStcockBill",
    "dtFractUnit",
    "dtSearchGoods",
    "dtStockBillDetail",
    "CombinationDetail",
    "dtSerialNumber",
    "GoodsPermissions"
   ]
}
]]></request></batch>
"""

    def __init__(self, go_next_page=False, history=False):
        super(PurchaseStoreOrder, self).__init__()
        self.__go_next_page = go_next_page
        self.__history = history

    def get_request_data(self):
        start_date = Date(self._start_time).format_es_old_utc() if self._start_time else Date.now().plus_days(
            -1).to_day_start().format_es_old_utc()
        end_date = Date(self._end_time).format_es_old_utc() if self._end_time else \
            Date.now().format_es_old_utc()
        days, his = (90, 'true') if self.__history else (0, 'false')
        return self.request_data % (days, start_date, end_date, his, self._page_size, self._page)

    def get_unique_define(self):
        return merge_str(
            'purchase_store_order',
            self._start_time,
            self._end_time,
            self._page_size,
            self._page,
        )

    def parse_response(self, response, task):
        # 爬虫的抓取时间
        sync_time = Date.now().format_es_utc_with_tz()
        # json 结果
        result = self.detect_xml_text(response.text)
        if len(result['data']['data']):
            for _order in result['data']['data']:
                _order['sync_time'] = sync_time
                stock_uid = _order['stock_uid']
                self.crawl_handler_page(
                    PurchaseStoreOrderGoods(stock_uid).set_priority(PurchaseStoreOrderGoods.CONST_PRIORITY_BUNDLED))
                self.send_message(_order, merge_str('purchase_store_order', _order.get('stock_code', '')))
            EsPurchaseOrder().update(result['data']['data'], async=True)
            self.crawl_next_page()
        return {
            # 'text': response.text,
            'start_time': self._start_time,
            'end_time': self._end_time,
            'page_size': self._page_size,
            'page': self._page,
            'next_page': self.__go_next_page,
        }

    def crawl_next_page(self):
        """
        爬下一页
        :return:
        """
        if self.__go_next_page and not self.check_flag(self.CONST_FLAG_BREAK) and self.in_processor():
            self.crawl_handler_page(
                PurchaseStoreOrder(go_next_page=self.__go_next_page, history=self.__history)
                    .set_page(self._page + 1)
                    .set_page_size(self._page_size)
                    .set_start_time(self._start_time)
                    .set_end_time(self._end_time)
                    .set_priority(self._priority)
            )

    @staticmethod
    def run_days(start_time, end_time, history=False, priority=0):
        """
        更新指定时间区间的数据
        :param start_time: 开始时间，eg. Date.now().to_day_start().format()
        :param end_time: 结束时间，eg. Date.now().to_day_end().format()
        :param priority:
        :param history:
        :return:
        """
        PurchaseStoreOrder(go_next_page=True, history=history) \
            .set_priority(priority) \
            .set_start_time(start_time) \
            .set_end_time(end_time) \
            .enqueue()

from hupun.page.base import *
from hupun_refund.model.es.order_refund import OrderRefund as ORefundEs
from hupun_refund.page.order_refund_exchange_info import OrderRefundExchange
from hupun_refund.page.order_refund_info import OrderRefundInfo
from hupun_refund.page.order_refund_operation import OrderRefundOperation


class OrderRefund(Base):
    """
    商品售后单 的数据
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
   "action":"load-data",
   "dataProvider":"exchangeInterceptor#queryExchangeList",
   "supportsEntity":true,
   "parameter":{
     "dateType":1,
     "history":false,
     "startDate":"%s",
     "endDate":"%s",
     "view_name":"exchange.query",
     "exactType":1,
     "$dataType":"dtExchangeSearch"
     },
   "resultDataType":"v:exchange.query$[dtExchange]",
   "pageSize":"%d",
   "pageNo":%d,
   "context":{},
   "loadedDataTypes":[
     "Region",
     "dtSearch",
     "dtExchange",
     "Country",
     "Shop",
     "dtError",
     "dtExchangeSearch",
     "GoodsSpec",
     "Storage",
     "Trade",
     "dtTradeAddition",
     "dtTradeStatement",
     "dtExchangeRecord",
     "TradeLog",
     "dtJzPartner",
     "Order",
     "dtInvoice",
     "GoodsPermissions",
     "dtSalePacking",
     "dtSearchGoods",
     "dtBatch",
     "dtSerialNumber",
     "dtMultiBarcode",
     "dtGoodsUniqueCode",
     "dtJzPartnerNew"
   ]
 }
]]></request>
</batch>
"""

    def __init__(self, go_next_page=False):
        super(OrderRefund, self).__init__()
        self.__go_next_page = go_next_page

    def get_request_data(self):
        start_date = Date(self._start_time).to_day_start().format_es_old_utc() if self._start_time else \
            Date.now().to_day_start().format_es_old_utc()
        end_date = Date(self._end_time).format_es_old_utc() if self._end_time else \
            Date.now().format_es_old_utc()
        return self.request_data % (start_date, end_date, self._page_size, self._page)

    def get_unique_define(self):
        return merge_str('order_refund', self._page, self._page_size, self._start_time, self._end_time)

    def parse_response(self, response, task):
        # 爬虫的抓取时间
        sync_time = Date.now().format_es_utc_with_tz()
        # json 结果
        result = self.detect_xml_text(response.text)
        if len(result['data']['data']):
            for _item in result['data']['data']:
                _item['sync_time'] = sync_time
                sys_shop = _item['sys_shop']
                exchange_uid = _item['exchange_uid']
                exchange_no = _item['exchange_no']
                exchange_type = _item['exchange_type']
                _item['tp_tids'] = _item['tp_tid'].split('|')

                if exchange_type == 2:
                    # 开始抓取 exchange 等于 2 的数据
                    self.crawl_handler_page(OrderRefundExchange(sys_shop, exchange_uid, exchange_no).set_priority(
                        OrderRefundExchange.CONST_PRIORITY_BUNDLED).use_cookie_pool(self._use_cookie_pool))
                    # 开始获取由于换货而新增的线下订单
                    self.crawl_handler_page(OrderRefundOperation(sys_shop, exchange_uid, exchange_no).set_priority(
                        OrderRefundOperation.CONST_PRIORITY_BUNDLED).use_cookie_pool(self._use_cookie_pool))

                # 获取 商品售后单的订单商品 数据并写入
                self.crawl_handler_page(OrderRefundInfo(sys_shop, exchange_uid, exchange_no).set_priority(
                    OrderRefundInfo.CONST_PRIORITY_BUNDLED).use_cookie_pool(self._use_cookie_pool))

                # self.send_message(_item, merge_str('order_refund',
                #                                    _item.get('sys_shop', ''),
                #                                    _item.get('exchange_uid', ''),
                #                                    _item.get('exchange_no', '')))
            # 这个异步更新数据需要开启 es 队列去消费
            ORefundEs().update(result['data']['data'], async=True)
            # 抓取下一页
            self.crawl_next_page()
        return {
            'tag': '淘宝售后单',
            # 'text': response.text,
            'page': self._page,
            'start_time': self._start_time,
            'end_time': self._end_time,
        }

    def crawl_next_page(self):
        """
        爬下一页
        :return:
        """
        if self.__go_next_page and not self.check_flag(self.CONST_FLAG_BREAK) and self.in_processor():
            self.crawl_handler_page(
                OrderRefund(go_next_page=self.__go_next_page)
                    .set_page(self._page + 1)
                    .set_page_size(self._page_size)
                    .set_start_time(self._start_time)
                    .set_end_time(self._end_time)
                    .set_priority(self._priority)
                    .use_cookie_pool(self._use_cookie_pool)
            )

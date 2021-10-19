from hupun.page.base import *
from hupun_refund.model.es.taobao_refund import TaobaoRefund as TRefundEs
from hupun_refund.page.taobao_refund_info import TaobaoRefundInfo


class TaobaoRefund(Base):
    """
    淘宝售后单 的数据
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
   "action":"load-data",
   "dataProvider":"exchangeInterceptor#queryOnlineRefund",
   "supportsEntity":true,
   "parameter":{
     "days":"0",
     "start_date":"%s",
     "end_date":"%s",
     "untreated":"0",
     "view":"exchange.online_refund",
     "history":false,
     "$dataType":"v:exchange.online_refund$dtSearch"
   },
   "resultDataType":"v:exchange.online_refund$[dtOnineRefund]",
   "pageSize":"%d",
   "pageNo":%d,
   "context":{},
   "loadedDataTypes":[
     "dtProof",
     "dtRefuseReason",
     "ElectronExpress",
     "dtSearch",
     "dtRefundStatus",
     "dtMsgCode",
     "Shop",
     "dtError",
     "dtSyncRefund",
     "Trade",
     "dtOnineRefund",
     "dtJzPartner",
     "dtSearchGoods",
     "dtSalePacking",
     "dtExchangeRecord",
     "Order",
     "dtTradeStatement",
     "TradeLog",
     "dtTradeAddition",
     "dtInvoice",
     "dtSerialNumber",
     "dtMultiBarcode",
     "dtGoodsUniqueCode",
     "dtJzPartnerNew",
     "dtBatch"
   ]
 }
]]></request>
</batch>
"""

    def __init__(self, go_next_page=False):
        super(TaobaoRefund, self).__init__()
        self.__go_next_page = go_next_page

    def get_request_data(self):
        start_date = Date(self._start_time).to_day_start().format_es_old_utc() if self._start_time else \
            Date.now().to_day_start().format_es_old_utc()
        end_date = Date(self._end_time).format_es_old_utc() if self._end_time else \
            Date.now().format_es_old_utc()
        return self.request_data % (start_date, end_date, self._page_size, self._page)

    def get_unique_define(self):
        return merge_str('taobao_refund', self._page, self._page_size, self._start_time, self._end_time)

    def parse_response(self, response, task):
        # 爬虫的抓取时间
        sync_time = Date.now().format_es_utc_with_tz()
        # json 结果
        result = self.detect_xml_text(response.text)
        if len(result['data']['data']):
            for _item in result['data']['data']:
                _item['sync_time'] = sync_time

                # 获取淘宝售后单对应的商品详情
                refund_no = _item['refund_no']
                ol_oid = _item['ol_oid']
                sys_shop = _item['sys_shop']
                ol_refund = _item['ol_refund']
                com_uid = _item['com_uid']
                exchange_no = _item['exchange_no']
                shop_type = _item['shop_type']
                self.crawl_handler_page(
                    TaobaoRefundInfo(ol_oid, sys_shop, ol_refund, com_uid, exchange_no, shop_type, refund_no)
                        .use_cookie_pool(self._use_cookie_pool))

                # 取消保存数据到mongo
                # self.send_message(_item, merge_str('taobao_refund', _item.get('refund_no', '')))
            # 这个异步更新数据需要开启 es 队列去消费
            TRefundEs().update(result['data']['data'], async=True)
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
                TaobaoRefund(go_next_page=self.__go_next_page)
                    .set_page(self._page + 1)
                    .set_page_size(self._page_size)
                    .set_start_time(self._start_time)
                    .set_end_time(self._end_time)
                    .set_priority(self._priority)
                    .use_cookie_pool(self._use_cookie_pool)
            )

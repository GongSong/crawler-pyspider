from hupun.page.base import *
from hupun_refund.model.es.order_refund_exchange_info import OrderRefundExchange as OExchangeEs


class OrderRefundExchange(Base):
    """
    退货订单 exchange 商品 的数据
    """
    request_data = """
<batch><request type="json"><![CDATA[
 {
   "action": "load-data",
   "dataProvider": "exchangeInterceptor#getExchangeOrder",
   "supportsEntity": true,
   "parameter": {
     "history": false,
     "shopUid": "%s",
     "exchangeUid": "%s",
     "order_type": "1"
   },
   "resultDataType": "v:exchange.query$[Order]",
   "context": {},
   "loadedDataTypes": [
     "Region",
     "Shop",
     "dtError",
     "dtExchangeSearch", 
     "dtExchange",
     "GoodsSpec",
     "Storage",
     "dtSearch",
     "Trade",
     "dtExchangeRecord",
     "dtSearchGoods",
     "dtJzPartner",
     "TradeLog",
     "dtSalePacking",
     "dtInvoice",
     "dtTradeAddition",
     "Order",
     "GoodsPermissions",
     "dtBatch",
     "dtJzPartnerNew",
     "dtSerialNumber"
   ]
 }
]]></request></batch>
"""

    def __init__(self, sys_shop, exchange_uid, exchange_no):
        super(OrderRefundExchange, self).__init__()
        self.__sys_shop = sys_shop
        self.__exchange_uid = exchange_uid
        self.__exchange_no = exchange_no

    def get_request_data(self):
        return self.request_data % (self.__sys_shop, self.__exchange_uid)

    def get_unique_define(self):
        return merge_str('refund_exchange_info', self.__sys_shop, self.__exchange_uid)

    def parse_response(self, response, task):
        # 爬虫的抓取时间
        sync_time = Date.now().format_es_utc_with_tz()
        # json 结果
        result = self.detect_xml_text(response.text)
        if len(result['data']):
            for _item in result['data']:
                sys_sku_id = _item['sys_sku_id']
                if not sys_sku_id:
                    processor_logger.info("pass because exchange sku id doesn't exists!")
                    result['data'].remove(_item)
                    continue
                _item['sync_time'] = sync_time
                _item['exchange_no'] = self.__exchange_no
                _item['combine_keys'] = '_'.join([self.__sys_shop, self.__exchange_uid, sys_sku_id])
                # self.send_message(_item, merge_str('order_refund_exchange_info', _item['combine_keys']))

            # 这个异步更新数据需要开启 es 队列去消费
            OExchangeEs().update(result['data'], async=True)
        return {
            'tag': '退货订单 exchange 商品 的数据',
            # 'text': response.text,
            'sys_shop': self.__sys_shop,
            'exchange_uid': self.__exchange_uid,
            'exchange_no': self.__exchange_no,
        }

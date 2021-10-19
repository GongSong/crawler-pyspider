from hupun.page.base import *
from hupun_refund.model.es.order_refund_info import OrderRefundInfo as OInfoEs


class OrderRefundInfo(Base):
    """
    商品售后单商品详情 的数据
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
   "action":"load-data",
   "dataProvider":"exchangeInterceptor#getExchangeOrder",
   "supportsEntity":true,
   "parameter":{
     "shopUid":"%s",
     "exchangeUid":"%s",
     "order_type":0,
     "distr_uid":null,
     "history":false,
     "exchange_no":"%s"
   },
   "resultDataType":"v:exchange.query$[Order]",
   "context":{},
   "loadedDataTypes":[
     "Storage",
     "Country",
     "dtSearch",
     "Region",
     "dtExchangeSearch",
     "GoodsSpec",
     "Shop",
     "dtExchange",
     "dtError",
     "Trade",
     "dtTradeStatement",
     "GoodsPermissions",
     "dtSearchGoods",
     "dtJzPartner",
     "dtTradeAddition",
     "dtInvoice",
     "dtExchangeRecord",
     "dtSalePacking",
     "TradeLog",
     "Order",
     "dtMultiBarcode",
     "dtGoodsUniqueCode",
     "dtJzPartnerNew",
     "dtBatch",
     "dtSerialNumber"
   ]
 }
]]></request>
</batch>
"""

    def __init__(self, sys_shop, exchange_uid, exchange_no):
        super(OrderRefundInfo, self).__init__()
        self.__sys_shop = sys_shop
        self.__exchange_uid = exchange_uid
        self.__exchange_no = exchange_no

    def get_request_data(self):
        return self.request_data % (self.__sys_shop, self.__exchange_uid, self.__exchange_no)

    def get_unique_define(self):
        return merge_str('order_refund_info', self.__sys_shop, self.__exchange_uid, self.__exchange_no)

    def parse_response(self, response, task):
        # 爬虫的抓取时间
        sync_time = Date.now().format_es_utc_with_tz()
        # json 结果
        result = self.detect_xml_text(response.text)
        if len(result['data']):
            for _item in result['data']:
                tp_sku_id = _item['tp_sku_id']
                if not tp_sku_id:
                    processor_logger.info("pass because tp_sku_id doesn't exists!")
                    result['data'].remove(_item)
                    continue
                _item['sync_time'] = sync_time
                _item['exchange_no'] = self.__exchange_no
                _item['combine_keys'] = '_'.join([self.__exchange_no, tp_sku_id])
                # self.send_message(_item, merge_str('order_refund_info', _item['combine_keys']))

            # 这个异步更新数据需要开启 es 队列去消费
            OInfoEs().update(result['data'], async=True)
        return {
            'tag': '商品售后单商品详情 的数据',
            # 'text': response.text,
            'sys_shop': self.__sys_shop,
            'exchange_uid': self.__exchange_uid,
            'exchange_no': self.__exchange_no,
        }

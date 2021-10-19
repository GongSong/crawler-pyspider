from hupun.page.base import *
from hupun_refund.model.es.taobao_refund_info import TaobaoRefundInfo as TRefundInfoEs


class TaobaoRefundInfo(Base):
    """
    淘宝售后单 商品详情 的数据
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
   "action":"load-data",
   "dataProvider":"exchangeInterceptor#getOnlineRefundOrder",
   "supportsEntity":true,
   "parameter":{
     "tp_oid":"%s",
     "sys_shop":"%s",
     "ol_refund":"%s",
     "com_uid":"%s",
     "exchange_no":"%s",
     "shop_type":"%s"
   },
   "resultDataType":"v:exchange.online_refund$[Order]",
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

    def __init__(self, ol_oid, sys_shop, ol_refund, com_uid, exchange_no, shop_type, refund_no):
        super(TaobaoRefundInfo, self).__init__()
        self.__ol_oid = ol_oid
        self.__sys_shop = sys_shop
        self.__ol_refund = ol_refund
        self.__com_uid = com_uid
        self.__exchange_no = exchange_no
        self.__shop_type = shop_type
        self.__refund_no = refund_no

    def get_request_data(self):
        return self.request_data % (
            self.__ol_oid,
            self.__sys_shop,
            self.__ol_refund,
            self.__com_uid,
            self.__exchange_no,
            self.__shop_type
        )

    def get_unique_define(self):
        return merge_str(
            'taobao_refund_info',
            self.__ol_oid,
            self.__sys_shop,
            self.__ol_refund,
            self.__com_uid,
            self.__exchange_no,
            self.__shop_type
        )

    def parse_response(self, response, task):
        # 爬虫的抓取时间
        sync_time = Date.now().format_es_utc_with_tz()
        # json 结果
        result = self.detect_xml_text(response.text)
        if len(result['data']):
            for _item in result['data']:
                _item['sync_time'] = sync_time
                tp_sku_id = _item['tp_sku_id']

                # combine_keys 作为本 index 的主键，因为主键是组合起来的
                _item['combine_keys'] = '_'.join([self.__refund_no, tp_sku_id])

                # self.send_message(_item, merge_str('taobao_refund_info', _item['combine_keys']))
            # 这个异步更新数据需要开启 es 队列去消费
            TRefundInfoEs().update(result['data'], async=True)
        return {
            'tag': '淘宝售后单商品详情数据',
            # 'text': response.text,
            'refund_no': self.__refund_no,
        }

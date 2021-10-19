from hupun.page.base import *
from hupun_refund.model.es.order_refund import OrderRefund as ORefundEs


class OrderRefundOperation(Base):
    """
    由于换货而新增的线下订单 的数据
    """
    request_data = """
<batch>
<request type="json"><![CDATA[{
    "action": "load-data",
    "dataProvider": "exchangeInterceptor#getRecord",
    "supportsEntity": true,
    "parameter": {
     "history": false,
     "exchangeUid": "%s"
    },
    "resultDataType": "v:exchange.list$[dtExchangeRecord]",
    "context": {},
    "loadedDataTypes": [
     "dtOperate",
     "Trade",
     "Region",
     "Shop",
     "GoodsSpec",
     "dtExchangeSearch",
     "FinBill",
     "dtError",
     "dtExchange",
     "dtSearch",
     "Storage",
     "FinAccount",
     "dtExchangeRecord",
     "Order",
     "dtSalePacking",
     "dtJzPartner",
     "GoodsPermissions",
     "dtTradeAddition",
     "TradeLog",
     "dtInvoice",
     "dtSearchGoods",
     "dtSerialNumber",
     "dtBatch",
     "dtJzPartnerNew"
    ]
    }]]></request>
</batch>
"""

    def __init__(self, sys_shop, exchange_uid, exchange_no):
        super(OrderRefundOperation, self).__init__()
        self.__sys_shop = sys_shop
        self.__exchange_uid = exchange_uid
        self.__exchange_no = exchange_no

    def get_request_data(self):
        return self.request_data % self.__exchange_uid

    def get_unique_define(self):
        return merge_str('order_refund_operation', self.__exchange_uid)

    def parse_response(self, response, task):
        # 爬虫的抓取时间
        sync_time = Date.now().format_es_utc_with_tz()
        # json 结果
        result = self.detect_xml_text(response.text)
        if len(result['data']):
            save_item = dict()
            save_item['sys_shop'] = self.__sys_shop
            save_item['exchange_uid'] = self.__exchange_uid
            save_item['exchange_no'] = self.__exchange_no
            save_item['sync_time'] = sync_time
            for _item in result['data']:
                detail = _item['record_detail']
                if 'XD' in detail:
                    save_item['xd_order'] = 'XD' + detail.split('XD', 1)[1].strip()
                    # self.send_message(save_item, merge_str('order_refund',
                    #                                        save_item.get('sys_shop', ''),
                    #                                        save_item.get('exchange_uid', ''),
                    #                                        save_item.get('exchange_no', '')))
                    # 这个异步更新数据需要开启 es 队列去消费
                    ORefundEs().update([save_item], async=True)
                    break
        return {
            'tag': '由于换货而新增的线下订单',
            # 'text': response.text,
            'sys_shop': self.__sys_shop,
            'exchange_uid': self.__exchange_uid,
            'exchange_no': self.__exchange_no,
        }

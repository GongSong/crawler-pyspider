from hupun.page.base import *
from hupun.model.es.order_goods import OrderGoods as EsOrderGoods


class OrderGoods(Base):
    request_data = """
<batch><request type="json"><![CDATA[
{
  "action": "load-data",
  "dataProvider": "saleInterceptor#getOrders",
  "supportsEntity": true,
  "parameter": {
    "tradeUid": "%s",
    "storageUid": "%s",
    "history": %s,
    "view": "sale.query"
  },
  "resultDataType": "v:sale.query$[Order]",
  "context": {},
  "loadedDataTypes": [
    "dtQueryCondition",
    "dtMarkType",
    "Order",
    "dtSearchHistory",
    "dtInvoice",
    "dtButtonDiy",
    "MultiOper",
    "Storage",
    "Oper",
    "MultiShop",
    "dtSearch",
    "Shop",
    "dtCombination",
    "Region",
    "GoodsSpec",
    "dtButton",
    "dtSide",
    "operBillType",
    "MultiStorage",
    "Trade",
    "CombinationGoods",
    "PrintConfig",
    "Template",
    "batchInventory",
    "dtStorage",
    "dtTradeStatement",
    "GoodsPermissions",
    "dtJzPartner",
    "dtMultiBarcode",
    "dtSalePacking",
    "dtSearchGoods",
    "TradeLog",
    "dtGoodsUniqueCode",
    "dtSerialNumber",
    "dtBatch",
    "dtTradeAddition",
    "dtJzPartnerNew"
  ]
}
]]></request></batch>
"""

    def __init__(self, trade_uid, storage_uid, tp_tid, trade_create_time, is_old=False):
        super(OrderGoods, self).__init__()
        self.__trade_uid = trade_uid
        self.__storage_uid = storage_uid
        self.__tp_tid = tp_tid
        self.__trade_create_time = trade_create_time
        self.__is_old = is_old
        self._priority = self.CONST_PRIORITY_BUNDLED

    def get_request_data(self):
        return self.request_data % (self.__trade_uid, self.__storage_uid, 'true' if self.__is_old else 'false')

    def get_unique_define(self):
        return merge_str('order_goods', self.__trade_uid, self.__storage_uid)

    def parse_response(self, response, task):
        sync_time = Date.now().format_es_utc_with_tz()
        result = self.detect_xml_text(response.text)
        for _order_goods in result['data']:
            # 保证商品数据的唯一性, 额外添加的字段sku_id, 如果订单中的商品在万里牛erp不存在, 取第三方平台的sku
            _order_goods['sku_id'] = _order_goods['spec_code']
            if not _order_goods['sku_id']:
                _order_goods['sku_id'] = _order_goods['tp_outer_sku_id']
            if not _order_goods['sku_id']:
                processor_logger.error("商品的barcode找不到: %s" % str(_order_goods))
                continue
            if not _order_goods['tp_tid']:
                _order_goods['tp_tid'] = self.__tp_tid
            _order_goods['sync_time'] = sync_time
            _order_goods['trade_create_time'] = self.__trade_create_time
            # 取消保存数据到mongo
            # self.send_message(_order_goods,
            #                   merge_str('order_goods',
            #                             _order_goods.get('sys_trade', ''),
            #                             _order_goods.get('sku_id', ''),
            #                             _order_goods.get('tp_tid', '')))
        EsOrderGoods().update(result['data'], async=True)
        return {
            # 'text': response.text,
            'trade_uid': self.__trade_uid,
            'storage_uid': self.__storage_uid,
            'is_old': self.__is_old
        }

from hupun.page.base import *


class SplitOrderGoods(Base):
    """
    在订单审核页面,根据订单号对应的uid查询需要拆分的订单对应的所有商品
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
  "action": "load-data",
  "dataProvider": "saleInterceptor#getOrders",
  "supportsEntity": true,
  "parameter": {
    "tradeUid": "%s",
    "storageUid": "%s",
    "history": %s,
    "view": "sale.approve"
  },
  "resultDataType": "v:sale.approve$[Order]",
  "context": {},
  "loadedDataTypes": [
    "dtException",
    "dtCombination",
    "dtUnmerge",
    "dtSearch",
    "operBillType",
    "GoodsSpec",
    "Trade",
    "dtTradeStatementDetail",
    "dtMarkType",
    "dtStorage",
    "Oper",
    "Country",
    "Order",
    "Storage",
    "FinAccount",
    "batchInventory",
    "CustomAddress",
    "dtCheckExp",
    "TradeUnmergeRule",
    "dtQueryCondition",
    "MultiShop",
    "dtButton",
    "MultiOper",
    "dtModGoods",
    "Shop",
    "dtInvoice",
    "CombinationGoods",
    "SysLogisticsType",
    "dtButtonDiy",
    "MultiStorage",
    "dtErrorType",
    "dtSide",
    "Region",
    "GoodsPermissions",
    "dtSerialNumber",
    "dtSearchGoods",
    "dtGoodsUniqueCode",
    "dtMultiBarcode",
    "dtTradeStatement",
    "dtJzPartner",
    "Goods",
    "TradeLog",
    "dtBatch",
    "dtTradeAddition",
    "dtSalePacking",
    "dtJzPartnerNew"
  ]
 }
]]></request>
</batch>
"""

    def __init__(self, trade_uid, storage_uid, history):
        super(SplitOrderGoods, self).__init__()
        self.__trade_uid = trade_uid
        self.__storage_uid = storage_uid
        self.__history = history

    def get_request_data(self):
        req_data = self.request_data % (self.__trade_uid, self.__storage_uid, self.__history)
        return req_data

    def get_unique_define(self):
        return merge_str('split_order_goods', self.__trade_uid)

    def parse_response(self, response, task):
        # json 结果
        result = self.detect_xml_text(response.text)
        return_result = result['data']
        return return_result

from hupun.page.base import *


class OrderNumQuery(Base):
    """
    在订单审核页面根据订单号查询需要拆分的订单
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
  "action": "load-data",
  "dataProvider": "saleInterceptor#queryTrade",
  "supportsEntity": true,
  "parameter": {
    "buyerType": "1",
    "dateType": 2,
    "history": false,
    "NOSIZE": "true",
    "view": "sale.approve",
    "showModify": false,
    "refund": false,
    "detail": 0,
    "containsPackage": false,
    "noSpecContainsPkg": false,
    "unRelated": false,
    "canMerge": false,
    "exactType": 1,
    "tp_tid": "%s",
    "$dataType": "dtSearch"
  },
  "resultDataType": "v:sale.approve$[Trade]",
  "pageSize": 100,
  "pageNo": 1,
  "context": {},
  "loadedDataTypes": [
    "TradeUnmergeRule",
    "FinAccount",
    "dtInvoice",
    "dtMarkType",
    "batchInventory",
    "SysLogisticsType",
    "CombinationGoods",
    "dtSide",
    "MultiOper",
    "dtErrorType",
    "dtCombination",
    "dtSearch",
    "CustomAddress",
    "dtQueryCondition",
    "Oper",
    "operBillType",
    "GoodsSpec",
    "Storage",
    "dtCheckExp",
    "Region",
    "dtStorage",
    "MultiShop",
    "dtUnmerge",
    "Shop",
    "MultiStorage",
    "dtTradeStatementDetail",
    "Country",
    "Order",
    "Trade",
    "dtButtonDiy",
    "dtModGoods",
    "dtButton",
    "dtException",
    "dtSalePacking",
    "dtJzPartner",
    "TradeLog",
    "dtTradeAddition",
    "Goods",
    "GoodsPermissions",
    "dtGoodsUniqueCode",
    "dtSerialNumber",
    "dtSearchGoods",
    "dtTradeStatement",
    "dtBatch",
    "dtMultiBarcode",
    "dtJzPartnerNew"
  ]
 }
]]></request>
</batch>
"""

    def __init__(self, tp_tid):
        super(OrderNumQuery, self).__init__()
        self.__tp_tid = tp_tid

    def get_request_data(self):
        req_data = self.request_data % self.__tp_tid
        return req_data

    def get_unique_define(self):
        return merge_str('order_number_query', self.__tp_tid)

    def parse_response(self, response, task):
        # json 结果
        result = self.detect_xml_text(response.text)
        return_result = result['data']['data']
        return return_result

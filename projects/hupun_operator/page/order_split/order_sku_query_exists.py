from hupun.page.base import *


class OrderSkuQueryExists(Base):
    """
    在订单审核页面根据sku号查询该商品是否存在订单中
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
  "action": "load-data",
  "dataProvider": "goodsInterceptor#queryGoodsQuick",
  "supportsEntity": true,
  "parameter": {
    "condition": "%s",
    "includeEmpty": "true",
    "keyWordType": null,
    "showPackage": null,
    "itemInventories": false,
    "storageUid": null,
    "storageUidTgt": null,
    "distr_uid": null
  },
  "resultDataType": "v:sale.approve$[GoodsSpec]",
  "pageSize": 0,
  "pageNo": 1,
  "context": {},
  "loadedDataTypes": [
    "MultiShop",
    "dtSearch",
    "FinAccount",
    "operBillType",
    "GoodsSpec",
    "Storage",
    "dtErrorType",
    "SysLogisticsType",
    "Country",
    "dtCheckExp",
    "dtModGoods",
    "Oper",
    "MultiStorage",
    "dtInvoice",
    "Trade",
    "dtUnmerge",
    "Order",
    "Shop",
    "dtMarkType",
    "batchInventory",
    "TradeUnmergeRule",
    "Region",
    "CombinationGoods",
    "dtStorage",
    "dtException",
    "MultiOper",
    "dtButtonDiy",
    "dtQueryCondition",
    "dtTradeStatementDetail",
    "dtCombination",
    "dtSide",
    "dtButton",
    "CustomAddress",
    "dtMultiBarcode",
    "dtSerialNumber",
    "TradeLog",
    "dtGoodsUniqueCode",
    "dtSalePacking",
    "dtTradeAddition",
    "dtJzPartner",
    "dtBatch",
    "Goods",
    "dtTradeStatement",
    "GoodsPermissions",
    "dtSearchGoods",
    "dtJzPartnerNew"
  ]
 }
]]></request>
</batch>
"""

    def __init__(self, sku):
        super(OrderSkuQueryExists, self).__init__()
        self.__sku = sku

    def get_request_data(self):
        req_data = self.request_data % self.__sku
        return req_data

    def get_unique_define(self):
        return merge_str('order_sku_query_exitst', self.__sku)

    def parse_response(self, response, task):
        # json 结果
        result = self.detect_xml_text(response.text)
        return_result = result['data']
        return return_result

from hupun.page.base import *


class OrSkuReQuery(Base):
    """
    在订单审核页面根据商品sku查询对应的商品信息
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
    "includeEmpty": "false",
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
    "SysLogisticsType",
    "dtUnmerge",
    "dtMarkType",
    "dtStorage",
    "CustomAddress",
    "dtModGoods",
    "dtCombination",
    "dtInvoice",
    "GoodsSpec",
    "dtButtonDiy",
    "Trade",
    "operBillType",
    "CombinationGoods",
    "MultiOper",
    "dtTradeStatementDetail",
    "dtSearch",
    "TradeUnmergeRule",
    "dtErrorType",
    "Country",
    "Storage",
    "dtSide",
    "Oper",
    "Shop",
    "MultiShop",
    "FinAccount",
    "Region",
    "Order",
    "MultiStorage",
    "dtButton",
    "dtException",
    "dtCheckExp",
    "batchInventory",
    "dtQueryCondition",
    "dtGoodsUniqueCode",
    "dtMultiBarcode",
    "dtJzPartner",
    "Goods",
    "dtTradeStatement",
    "dtBatch",
    "dtSearchGoods",
    "TradeLog",
    "GoodsPermissions",
    "dtTradeAddition",
    "dtSerialNumber",
    "dtSalePacking",
    "dtJzPartnerNew"
  ]
 }
]]></request>
</batch>
"""

    def __init__(self, spec_code):
        super(OrSkuReQuery, self).__init__()
        self.__spec_code = spec_code

    def get_request_data(self):
        req_data = self.request_data % self.__spec_code
        return req_data

    def get_unique_define(self):
        return merge_str('order_sku_rename_query', self.__spec_code)

    def parse_response(self, response, task):
        # json 结果
        result = self.detect_xml_text(response.text)
        return result['data']

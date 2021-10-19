from hupun.page.base import *


class InvSyncGoodsSku(Base):
    """
    根据 商品编码 查询库存同步商品的sku信息
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
   "action": "load-data",
   "dataProvider": "inventoryInterceptor#queryInventory",
   "supportsEntity": true,
   "parameter": {
     "goodsUid": "%s",
     "alarm": false,
     "view": "inventory.sync",
     "isAutoWarn": null
   },
   "sysParameter": {},
   "resultDataType": "v:inventory.sync$[Inventory]",
   "context": {},
   "loadedDataTypes": [
     "Catagory",
     "WmsInventory",
     "SynPolicy",
     "GoodsSpec",
     "dtThirdStoInventory",
     "dtInvCondition",
     "bill",
     "MultiStorage",
     "ProductBrandMulti",
     "dtAsynCount",
     "Inventory",
     "dtShop",
     "Storage",
     "GoodsPermissions",
     "InventoryChangeBillDetail"
   ]
 }
]]></request>
</batch>
"""

    def __init__(self, goods_uid):
        super(InvSyncGoodsSku, self).__init__()
        self.__goods_uid = goods_uid

    def get_request_data(self):
        return self.request_data % self.__goods_uid

    def get_unique_define(self):
        return merge_str('inventory_sync_goods_sku', self.__goods_uid)

    def parse_response(self, response, task):
        # json 结果
        result = self.detect_xml_text(response.text)['data']
        return {
            'unique_name': 'inventory_sync_goods_sku',
            'length': len(response.content),
            'response': result
        }

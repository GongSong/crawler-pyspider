from hupun.page.base import *


class InvSyncGoods(Base):
    """
    根据 商品编码 查询库存同步商品的信息
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
   "action":"load-data",
   "dataProvider":"inventoryInterceptor#queryInventory",
   "supportsEntity":true,
   "parameter":{
     "alarm":false,
     "canInit":false,
     "sortBy1":false,
     "nosize":true,
     "brandUids":"",
     "brandNames":"-- 所有品牌 --",
     "view":"inventory.sync",
     "goodsCondition":"%s",
     "specCondition":""
   },
   "resultDataType":"v:inventory.sync$[Inventory]",
   "pageSize":"20",
   "pageNo":1,
   "context":{},
   "loadedDataTypes":[
     "bill",
     "Inventory",
     "MultiStorage",
     "Storage",
     "dtThirdStoInventory",
     "GoodsSpec",
     "ProductBrandMulti",
     "dtAsynCount",
     "dtShop",
     "dtInvCondition",
     "SynPolicy",
     "WmsInventory",
     "Catagory",
     "GoodsPermissions",
     "InventoryChangeBillDetail"
   ]
 }
]]></request>
</batch>
"""

    def __init__(self, goods_code):
        super(InvSyncGoods, self).__init__()
        self.__goods_code = goods_code

    def get_request_data(self):
        return self.request_data % self.__goods_code

    def get_unique_define(self):
        return merge_str('inventory_sync_goods', self.__goods_code)

    def parse_response(self, response, task):
        # json 结果
        result = self.detect_xml_text(response.text)['data']['data']
        return {
            'unique_name': 'inventory_sync_goods',
            'length': len(response.content),
            'response': result
        }

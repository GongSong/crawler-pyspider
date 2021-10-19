from hupun.page.base import *
from hupun_slow_crawl.model.es.store_house import StoreHouse


class GoodsInventorySpider(Base):
    """
    库存状况 的sku级别的总数
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
   "action":"remote-service",
   "service":"inventoryInterceptor#getInvTotalNum",
   "supportsEntity":true,
   "parameter":{
     "alarm":false,
     "canInit":false,
     "sortBy1":false,
     "nosize":false,
     "brandUids":"",
     "brandNames":"-- 所有品牌 --",
     "goodsType":0,
     "goodsTypeLable":"商品",
     "storageUids":"%s",
     "storageName":"-- 所有仓库 --",
     "storageType":"%s",
     "view":"inventory.info",
     "startQuantity":null,
     "endQuantity":null
   },
   "context":{},
   "loadedDataTypes":[
     "dtAsynCount",
     "GoodsSpec",
     "ProductBrandMulti",
     "Inventory",
     "WmsInventory",
     "Storage",
     "dtThirdStoInventory",
     "bill",
     "dtInvCondition",
     "Catagory",
     "MultiStorage",
     "GoodsPermissions",
     "InventoryChangeBillDetail"
   ]
 }
]]></request>
</batch>
"""

    def __init__(self):
        super(GoodsInventorySpider, self).__init__()
        storage_ids = StoreHouse().get_storage_ids()
        self.__storage_ids = storage_ids
        self.__storage_uids = ','.join(storage_ids) + ','
        self.__storage_type = '0,' * len(storage_ids)

    def get_request_data(self):
        return self.request_data % (self.__storage_uids, self.__storage_type)

    def get_unique_define(self):
        return merge_str('goods_inventory_spider', self.__storage_uids, self.__storage_type)

    def parse_response(self, response, task):
        # json 结果
        result = self.detect_xml_text(response.text)
        total_num = 0
        # total_price = 0
        if len(result['data']):
            total_num = int(result['data']['totalNum'])
            # total_price = float(result['data']['totalPrice'])
        return total_num

    def get_erp_numbers(self):
        '''收集万里牛爬虫得到的数量'''
        erp_numbers = GoodsInventorySpider() \
            .set_priority(GoodsInventorySpider.CONST_PRIORITY_BUNDLED) \
            .get_result()
        return erp_numbers

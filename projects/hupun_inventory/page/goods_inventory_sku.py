from hupun.page.base import *
from hupun_inventory.model.es.goods_inventory_sku import GoodsInventorySku as GoodsInveSkuEs


class GoodsInventorySku(Base):
    """
    库存状况 sku 标签的数据
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
   "action":"load-data",
   "dataProvider":"inventoryInterceptor#queryStorageDetail",
   "supportsEntity":true,
   "parameter":{
     "storageUids":"%s",
     "goods_uid":"%s",
     "spec_uid":"%s"
   },
   "resultDataType":"v:inventory.info$[Inventory]",
   "pageSize":0,
   "pageNo":1,
   "context":{},
   "loadedDataTypes":[
     "dtInvCondition",
     "Storage",
     "WmsInventory",
     "Inventory",
     "dtThirdStoInventory",
     "Catagory",
     "bill",
     "ProductBrandMulti",
     "GoodsSpec",
     "MultiStorage",
     "dtAsynCount",
     "GoodsPermissions",
     "InventoryChangeBillDetail"
   ]
 }
]]></request>
</batch>
"""

    def __init__(self, storage_ids, goods_uid, spec_uid, spec_code):
        super(GoodsInventorySku, self).__init__()
        self.__storage_uids = ','.join(storage_ids) + ','
        self.__goods_uid = goods_uid
        self.__spec_uid = spec_uid
        self.__spec_code = spec_code

    def get_request_data(self):
        return self.request_data % (self.__storage_uids, self.__goods_uid, self.__spec_uid)

    def get_unique_define(self):
        return merge_str('goods_inventory_sku', self.__goods_uid, self.__spec_uid)

    def parse_response(self, response, task):
        # 爬虫的抓取时间
        sync_time = Date.now().format_es_utc_with_tz()
        # json 结果
        result = self.detect_xml_text(response.text)
        if len(result['data']):
            for _item in result['data']:
                _item['sync_time'] = sync_time
                _item['spec_code'] = self.__spec_code
                self.send_message(_item, merge_str('goods_inventory_sku',
                                                   _item.get('itemID', ''),
                                                   _item.get('skuID', ''),
                                                   _item.get('storageID', '')))
            GoodsInveSkuEs().update(result['data'], async=True)

        return {
            'text': response.text[:200],
            'page': self._page,
        }

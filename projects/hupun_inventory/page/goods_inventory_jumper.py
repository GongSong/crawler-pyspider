from hupun.page.base import *
from hupun_inventory.page.goods_inventory_sku import GoodsInventorySku


class GoodsInventoryJumper(Base):
    """
    库存状况中间爬虫
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
   "action":"load-data",
   "dataProvider":"inventoryInterceptor#queryInventory",
   "supportsEntity":true,
   "parameter":{
     "goodsUid":"%s",
     "startQuantity":null,
     "endQuantity":null,
     "alarm":false,
     "view":"inventory.info",
     "isAutoWarn":null,
     "storageUids":"%s",
     "goodsType":0
   },
   "sysParameter":{},
   "resultDataType":"v:inventory.info$[Inventory]",
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

    def __init__(self, item_id, storage_ids):
        super(GoodsInventoryJumper, self).__init__()
        self.__storage_ids = storage_ids
        self.__item_id = item_id
        self.__storage_uids = ','.join(storage_ids) + ','

    def get_request_data(self):
        return self.request_data % (self.__item_id, self.__storage_uids)

    def get_unique_define(self):
        return merge_str('goods_inventory_jumper', self.__item_id)

    def parse_response(self, response, task):
        # json 结果
        result = self.detect_xml_text(response.text)
        if len(result['data']):
            for _item in result['data']:
                goods_uid = _item['itemID']
                spec_uid = _item['skuID']
                spec_code = _item['spec_code']
                self.crawl_handler_page(
                    GoodsInventorySku(self.__storage_ids, goods_uid, spec_uid, spec_code).set_priority(
                        GoodsInventorySku.CONST_PRIORITY_BUNDLED))
                self.send_message(_item, merge_str('goods_inventory_jumper',
                                                   _item.get('spec_code', ''),
                                                   _item.get('itemID', ''),
                                                   _item.get('skuID', '')))
        return {
            'text': response.text,
            'page': self._page,
        }

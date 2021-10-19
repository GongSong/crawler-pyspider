from hupun.page.base import *
from hupun_slow_crawl.model.es.inventory_sync_goods_sku_es import InvSyncGoodsSkuEs


class InvSyncGoodsAllSku(Base):
    """
    库存同步商品sku 的数据
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
    "Storage",
    "MultiStorage",
    "WmsInventory",
    "bill",
    "ProductBrandMulti",
    "dtThirdStoInventory",
    "SynPolicy",
    "dtAsynCount",
    "Catagory",
    "dtShop",
    "GoodsSpec",
    "Inventory",
    "dtInvCondition",
    "InventoryChangeBillDetail",
    "GoodsPermissions"
  ]
 }
]]></request>
</batch>
"""

    def __init__(self, goods_uid):
        super(InvSyncGoodsAllSku, self).__init__()
        self.__goods_uid = goods_uid

    def get_request_data(self):
        return self.request_data % self.__goods_uid

    def get_unique_define(self):
        return merge_str('inventory_sync_goods_all_sku', self.__goods_uid)

    def parse_response(self, response, task):
        # 爬虫的抓取时间
        sync_time = Date.now().format_es_utc_with_tz()
        # json 结果
        result = self.detect_xml_text(response.text)
        if len(result['data']):
            for _item in result['data']:
                _item['sync_time'] = sync_time
            # 这个异步更新数据需要开启 es 队列去消费
            InvSyncGoodsSkuEs().update(result['data'], async=True)
        return {
            'unique_name': 'inventory_sync_goods_all_sku',
            'result': result,
        }

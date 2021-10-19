from hupun.page.base import *
from hupun_inventory.model.es.goods_inventory import GoodsInventory as GoodsInveEs


class GoodsInventory(Base):
    """
    库存状况 标签的数据
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
     "goodsType":0,
     "goodsTypeLable":"商品",
     "storageUids":"%s",
     "storageName":"-- 所有仓库 --",
     "storageType":"%s",
     "view":"inventory.info",
     "startQuantity":null,
     "endQuantity":null
   },
   "resultDataType":"v:inventory.info$[Inventory]",
   "pageSize":"%d",
   "pageNo":%d,
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

    def __init__(self, storage_ids, to_next_page=False):
        super(GoodsInventory, self).__init__()
        self.__storage_ids = storage_ids
        self.__storage_uids = ','.join(storage_ids) + ','
        self.__storage_type = '0,' * len(storage_ids)
        self.__to_next_page = to_next_page

    def get_request_data(self):
        return self.request_data % (self.__storage_uids, self.__storage_type, self._page_size, self._page)

    def get_unique_define(self):
        return merge_str('goods_inventory', self.__storage_type, self._page_size, self._page)

    def parse_response(self, response, task):
        # 爬虫的抓取时间
        sync_time = Date.now().format_es_utc_with_tz()
        # json 结果
        result = self.detect_xml_text(response.text)
        if len(result['data']['data']):
            for _item in result['data']['data']:
                _item['sync_time'] = sync_time
                self.send_message(_item,
                                  merge_str('goods_inventory', _item.get('storageID', ''), _item.get('itemID', '')))
            GoodsInveEs().update(result['data']['data'], async=True)
            self.crawl_next_page()

        return {
            'text': response.text,
            'page': self._page,
        }

    def crawl_next_page(self):
        """
        爬下一页
        :return:
        """
        if self.__to_next_page and not self.check_flag(self.CONST_FLAG_BREAK) and self.in_processor():
            self.crawl_handler_page(GoodsInventory(self.__storage_ids, self.__to_next_page).
                                    set_page(self._page + 1).
                                    set_page_size(self._page_size).
                                    set_priority(self._priority))

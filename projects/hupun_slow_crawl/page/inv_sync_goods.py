from hupun.page.base import *
from hupun_slow_crawl.model.es.inventory_sync_goods_es import InvSyncGoodsEs
from hupun_slow_crawl.page.inv_sync_goods_sku import InvSyncGoodsAllSku


class InvSyncGoodsAll(Base):
    """
    库存同步商品 全量抓取的数据
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
  "action": "load-data",
  "dataProvider": "inventoryInterceptor#queryInventory",
  "supportsEntity": false,
  "parameter": {
    "alarm": false,
    "canInit": false,
    "sortBy1": false,
    "nosize": true,
    "brandUids": "",
    "brandNames": "-- 所有品牌 --",
    "view": "inventory.sync"
  },
  "resultDataType": "v:inventory.sync$[Inventory]",
  "pageSize": "%d",
  "pageNo": %d,
  "context": {}
 }
]]></request>
</batch>
"""

    def __init__(self, go_next_page=False):
        super(InvSyncGoodsAll, self).__init__()
        self.__go_next_page = go_next_page

    def get_request_data(self):
        return self.request_data % (self._page_size, self._page)

    def get_unique_define(self):
        return merge_str('inventory_sync_goods_all', self._page)

    def parse_response(self, response, task):
        # 爬虫的抓取时间
        sync_time = Date.now().format_es_utc_with_tz()
        # json 结果
        result = self.detect_xml_text(response.text)
        if len(result['data']['data']):
            for _item in result['data']['data']:
                _item['sync_time'] = sync_time
                goods_uid = _item['itemID']
                self.crawl_handler_page(
                    InvSyncGoodsAllSku(goods_uid).set_priority(InvSyncGoodsAllSku.CONST_PRIORITY_BUNDLED))
            # 这个异步更新数据需要开启 es 队列去消费
            InvSyncGoodsEs().update(result['data']['data'], async=True)
            # 抓取下一页
            self.crawl_next_page()
        return {
            'unique_name': 'inventory_sync_goods_all',
            'result': result,
        }

    def crawl_next_page(self):
        """
        爬下一页
        :return:
        """
        if self.__go_next_page and self.in_processor():
            self.crawl_handler_page(
                InvSyncGoodsAll(go_next_page=self.__go_next_page)
                    .set_page(self._page + 1)
                    .set_page_size(self._page_size)
                    .set_priority(self._priority)
            )

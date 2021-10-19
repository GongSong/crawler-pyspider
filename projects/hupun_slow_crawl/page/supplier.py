from hupun.page.base import *
from hupun_slow_crawl.model.es.supplier import Supplier as SupplierEs


class Supplier(Base):
    """
    供应商信息 的数据
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
   "action":"load-data",
   "dataProvider":"supplierInterceptor#querySupplier",
   "supportsEntity":true,
   "parameter":{
     "status":1,
     "balance":true
   },
   "resultDataType":"v:basic.SupplierDefend$[Supplier]",
   "pageSize":%d,
   "pageNo":%d,
   "context":{},
   "loadedDataTypes":[
     "StorageMulti",
     "PrdSupplier",
     "Storage",
     "Supplier",
     "Oper",
     "Region"
   ]
 }
]]></request>
</batch>
"""

    def __init__(self, go_next_page=False):
        super(Supplier, self).__init__()
        self.__go_next_page = go_next_page

    def get_request_data(self):
        return self.request_data % (self._page_size, self._page)

    def get_unique_define(self):
        return merge_str('supplier', self._page)

    def parse_response(self, response, task):
        # 爬虫的抓取时间
        sync_time = Date.now().format_es_utc_with_tz()
        # json 结果
        result = self.detect_xml_text(response.text)
        if len(result['data']['data']):
            for _item in result['data']['data']:
                _item['sync_time'] = sync_time
                self.send_message(_item, merge_str('supplier', _item.get('unitUid', '')))
            # 这个异步更新数据需要开启 es 队列去消费
            SupplierEs().update(result['data']['data'], async=True)
            # 抓取下一页
            self.crawl_next_page()
        return {
            'tag': '供应商信息',
            'text': response.text,
            'result': result,
            'page': self._page,
        }

    def crawl_next_page(self):
        """
        爬下一页
        :return:
        """
        if self.__go_next_page and not self.check_flag(self.CONST_FLAG_BREAK) and self.in_processor():
            self.crawl_handler_page(
                Supplier(go_next_page=self.__go_next_page)
                    .set_page(self._page + 1)
                    .set_page_size(self._page_size)
                    .set_priority(self._priority)
            )

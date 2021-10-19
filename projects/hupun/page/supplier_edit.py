from hupun.page.base import *
from hupun_slow_crawl.model.es.supplier import Supplier as SupplierEs


class SupplierEdit(Base):
    """
    供应商信息 的修改操作
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
   "action":"resolve-data",
   "dataResolver":"supplierInterceptor#updateSupplier",
   "dataItems":[
     {
       "alias":"dsSupplier",
       "data":{
         "$isWrapper":true,
         "$dataType":"v:basic.SupplierDefend$[Supplier]",
         "data":[
           {
             "unitUid":"EAF98C6386C43F81825AD9B629C409F9","comUid":"D1E338D6015630E3AFF2440F3CBBAFAD","unitCode":"0561","unitName":"test005","website":null,"province":null,"city":null,"area":null,"zip":null,"contact":null,"phone":null,"supplierType":0,"cellphone":"12097433455","email":null,"fax":null,"addr":null,"taxNumber":"123","bank":null,"remark":null,"initial":0,"balance":0,"advance":0,"occupy":0,"available":0,"supplier_name":null,"supplier_uid":null,"gradeUid":null,"gradeName":null,"rechargeBalance":0,"initialSum":0,"balanceSum":0,"status":1,"saleman":null,"salemanUid":null,"$dataType":"Supplier","$state":2,"$entityId":"136"
           }
         ]
       },
       "refreshMode":"value",
       "autoResetEntityState":true
     }
   ],
   "context":{}
 }
]]></request>
</batch>
"""

    def __init__(self):
        super(SupplierEdit, self).__init__()

    def get_request_data(self):
        return self.request_data % (self._page_size, self._page)

    def get_unique_define(self):
        return merge_str('supplier_edit', self._page)

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
        return {
            'tag': '供应商信息的修改操作',
            # 'text': response.text,
            'page': self._page,
        }

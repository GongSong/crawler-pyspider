import uuid

from hupun.page.base import *


class InventoryConfList(Base):
    """
    查询库存同步的手动上传配置和自动上传配置;
    手动和自动上传配置返回的内容都是相同的;
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
   "action":"load-data",
   "dataProvider":"synPolicyInterceptor#querySynPolicy",
   "supportsEntity":true,
   "resultDataType":"v:inventory.sync$[SynPolicy]",
   "pageSize":0,
   "pageNo":1,
   "context":{},
   "loadedDataTypes":[
     "dtShop",
     "Catagory",
     "SynPolicy",
     "GoodsSpec",
     "Inventory",
     "WmsInventory",
     "Storage",
     "ProductBrandMulti",
     "bill",
     "dtInvCondition",
     "dtAsynCount",
     "dtThirdStoInventory",
     "MultiStorage",
     "GoodsPermissions",
     "InventoryChangeBillDetail"
   ]
 }
]]></request>
</batch>
"""

    def __init__(self):
        super(InventoryConfList, self).__init__()

    def get_request_data(self):
        return self.request_data

    def get_unique_define(self):
        return merge_str('inventory_conf_list', uuid.uuid4())

    def parse_response(self, response, task):
        # json 结果
        result = self.detect_xml_text(response.text)['data']
        return {
            'unique_name': 'inventory_conf_list',
            'length': len(response.content),
            'response': result
        }

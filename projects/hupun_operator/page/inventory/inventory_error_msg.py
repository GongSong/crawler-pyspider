import uuid

from hupun.page.base import *


class InventoryErrorMsg(Base):
    """
    库存商品上传失败返回的错误信息
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
  "action":"remote-service",
  "service":"wizardService#getCurrentUploadInventoryCount",
  "supportsEntity":true,
  "context":{
  },
  "loadedDataTypes":[
    "Catagory",
    "dtAsynCount",
    "MultiStorage",
    "GoodsSpec",
    "Storage",
    "dtThirdStoInventory",
    "dtInvCondition",
    "dtShop",
    "WmsInventory",
    "Inventory",
    "bill",
    "SynPolicy",
    "ProductBrandMulti",
    "GoodsPermissions",
    "InventoryChangeBillDetail"]
 }
]]></request>
</batch>
"""

    def __init__(self):
        super(InventoryErrorMsg, self).__init__()

    def get_request_data(self):
        return self.request_data

    def get_unique_define(self):
        return merge_str('inventory_error_msg', uuid.uuid4())

    def parse_response(self, response, task):
        # json 结果
        result = self.detect_xml_text(response.text)['data']
        return {
            'unique_name': 'inventory_error_msg',
            'length': len(response.content),
            'response': result
        }

import uuid
from copy import deepcopy

from hupun.page.base import *


class InvUpload(Base):
    """
    库存同步的上传库存操作;
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
  "action": "resolve-data",
  "dataResolver": "inventoryInterceptor#saveInventory",
  "dataItems": [
    {
      "alias": "dsInventory",
      "data": {
        "$isWrapper": true,
        "$dataType": "v:inventory.sync$[Inventory]",
        "data": %s
      },
      "refreshMode": "value",
      "autoResetEntityState": true
    }
  ],
  "parameter": {
    "syn_config": %s,
    "view": "inventory.sync",
    "spec":""
  },
  "context": {}
 }
]]></request>
</batch>
"""

    def __init__(self, goods_data, sync_config):
        super(InvUpload, self).__init__()
        self.__goods_data = deepcopy(goods_data)
        self.__sync_config = deepcopy(sync_config)

    def get_request_data(self):
        # print('\nrequest_data', self.request_data % (json.dumps(self.__goods_data), json.dumps(self.__sync_config)),
        #       '\n')
        return self.request_data % (json.dumps(self.__goods_data), json.dumps(self.__sync_config))

    def get_unique_define(self):
        return merge_str('inventory_upload_operate', uuid.uuid4())

    def parse_response(self, response, task):
        # json 结果
        result = self.detect_xml_text(response.text)
        return {
            'unique_name': 'inventory_upload_operate',
            'length': len(response.content),
            'response': result
        }

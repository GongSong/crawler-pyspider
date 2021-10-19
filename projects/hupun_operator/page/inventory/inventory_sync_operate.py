import uuid
from copy import deepcopy

from hupun.page.base import *


class InvSyncOperate(Base):
    """
    查询库存同步的手动上传配置和自动上传配置;
    手动和自动上传配置返回的内容都是相同的;
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
    "action": "resolve-data",
    "dataResolver": "synPolicyInterceptor#saveSynPolicy",
    "dataItems": [
        {
            "alias": "dsSynPolicy",
            "data": {
                "$isWrapper": true,
                "$dataType": "v:inventory.sync$[SynPolicy]",
                "data": %s
            },
            "refreshMode": "value",
            "autoResetEntityState": true
        }
    ],
    "context": {}
}
]]></request>
</batch>
"""

    def __init__(self, sync_data):
        super(InvSyncOperate, self).__init__()
        self.__sync_data = deepcopy(sync_data)

    def get_request_data(self):
        return self.request_data % json.dumps(self.__sync_data)

    def get_unique_define(self):
        return merge_str('inventory_sync_operate', uuid.uuid4())

    def parse_response(self, response, task):
        # json 结果
        result = self.detect_xml_text(response.text)
        return {
            'unique_name': 'inventory_sync_operate',
            'length': len(response.content),
            'response': result
        }

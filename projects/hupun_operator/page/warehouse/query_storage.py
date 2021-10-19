from hupun.page.base import *


class QueryStorage(Base):
    """
    查询仓库
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
  "action": "load-data",
  "dataProvider": "storageInterceptor#queryStorage",
  "supportsEntity": true,
  "parameter": {
    "storageCode": "%s",
    "storageName": null,
    "status": null
  },
  "resultDataType": "v:basic.Storage$[dtStorage]",
  "pageSize": 20,
  "pageNo": 1,
  "context": {
    "switchContext": {}
  },
  "loadedDataTypes": [
    "dtStorage",
    "Storage"
  ]
 }
]]></request>
</batch>
"""

    def __init__(self, storage_code):
        super(QueryStorage, self).__init__()
        self.__storageCode = storage_code,

    def get_request_data(self):
        req_data = self.request_data % self.__storageCode
        return req_data

    def get_unique_define(self):
        return merge_str('query_storage', self.__storageCode)

    def parse_response(self, response, task):
        # json 结果
        result = response.text
        return self.detect_xml_text(result)['data']

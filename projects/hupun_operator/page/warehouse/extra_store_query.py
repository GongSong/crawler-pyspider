import uuid

from hupun.page.base import *


class ExtraStoreQuery(Base):
    """
    【仓库匹配】的例外店铺设置数据查询
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
  "action": "load-data",
  "dataProvider": "shopInterceptor#queryShopList_type",
  "supportsEntity": true,
  "parameter": {
    "status": 1
  },
  "resultDataType": "v:basic.StoragePolicy$[dtShop]",
  "pageSize": 0,
  "pageNo": 1,
  "context": {},
  "loadedDataTypes": [
    "dtCompany",
    "dtStorageRegionPolicy",
    "dtShop",
    "Region",
    "dtTypePolicyDetail",
    "dtCountry",
    "dtStorageAreaRegion",
    "MultiShop",
    "dtStorage",
    "dtCondition",
    "Allocation",
    "dtStorageRegionPolicyDetail",
    "Map",
    "Catagory",
    "dtPolicy"
  ]
 }
]]></request>
</batch>
"""

    def __init__(self):
        super(ExtraStoreQuery, self).__init__()

    def get_request_data(self):
        return self.request_data

    def get_unique_define(self):
        return merge_str('extra_store_query', uuid.uuid4())

    def parse_response(self, response, task):
        # json 结果
        result = self.detect_xml_text(response.text)['data']
        return result

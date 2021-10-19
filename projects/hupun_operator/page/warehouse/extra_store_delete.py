import uuid

from hupun.page.base import *


class ExtraStoreDelete(Base):
    """
    【仓库匹配】的例外店铺设置数据查询
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
  "action": "remote-service",
  "service": "shopInterceptor#updateShopToStoragePolicy",
  "supportsEntity": true,
  "parameter": {
    "shopUid": "%s",
    "shopName": "%s",
    "storageUid": null,
    "storageName": "%s",
    "oper": "del"
  },
  "context": {},
  "loadedDataTypes": [
    "dtPolicy",
    "Catagory",
    "dtStorageAreaRegion",
    "Allocation",
    "Map",
    "dtCountry",
    "dtStorageRegionPolicy",
    "Region",
    "dtTypePolicyDetail",
    "dtShop",
    "dtStorage",
    "dtCondition",
    "dtStorageRegionPolicyDetail",
    "dtCompany",
    "MultiShop"
  ]
 }
]]></request>
</batch>
"""

    def __init__(self, shop_uid, shop_name, storage_name):
        super(ExtraStoreDelete, self).__init__()
        self.__shop_uid = shop_uid
        self.__shop_name = shop_name
        self.__storage_name = storage_name

    def get_request_data(self):
        return self.request_data % (self.__shop_uid, self.__shop_name, self.__storage_name)

    def get_unique_define(self):
        return merge_str('extra_store_delete', uuid.uuid4())

    def parse_response(self, response, task):
        # json 结果
        result = self.detect_xml_text(response.text)
        return result

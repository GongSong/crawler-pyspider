import uuid

from hupun.page.base import *


class ExtraStoreSetting(Base):
    """
    【仓库匹配】的例外店铺设置操作
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
    "storageUid": "%s",
    "storageName": "%s"
  },
  "context": {},
  "loadedDataTypes": [
    "Map",
    "Catagory",
    "dtCondition",
    "Allocation",
    "dtStorageRegionPolicy",
    "dtStorageRegionPolicyDetail",
    "Region",
    "MultiShop",
    "dtStorage",
    "dtShop",
    "dtStorageAreaRegion",
    "dtPolicy",
    "dtCountry",
    "dtCompany",
    "dtTypePolicyDetail"
  ]
 }
]]></request>
</batch>
"""

    def __init__(self, shop_uid, shop_name, storage_uid, storage_name):
        super(ExtraStoreSetting, self).__init__()
        self.__shop_uid = shop_uid
        self.__shop_name = shop_name
        self.__storage_uid = storage_uid
        self.__storage_name = storage_name

    def get_request_data(self):
        return self.request_data % (self.__shop_uid, self.__shop_name, self.__storage_uid, self.__storage_name)

    def get_unique_define(self):
        return merge_str('extra_store_setting', uuid.uuid4())

    def parse_response(self, response, task):
        # json 结果
        result = self.detect_xml_text(response.text)
        return result

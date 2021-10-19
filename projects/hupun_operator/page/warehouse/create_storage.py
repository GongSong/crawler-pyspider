import uuid

from hupun.page.base import *


class CreateStorage(Base):
    """
    【仓库】创建
    """
    request_data = """
<batch>
<request type="json"><![CDATA[{"action":"resolve-data","dataResolver":"storageInterceptor#saveStorage","dataItems": [{"alias": "dsStorage","data": {"$isWrapper":true,"$dataType":"v:basic.Storage$[dtStorage]","data": [{"status":1,"categoryName":"正品仓","storageCode":"%s","storageName":"%s","province":"%s","city":"%s", "district":"%s","addr":"%s","contact":"%s","mobile":"%s","remark":"%s","$dataType":"v:basic.Storage$dtStorage","$state":1}]},"refreshMode":"value","autoResetEntityState":true}],"parameter": {"ext": {}},"context": {"switchContext": {}}}]]></request>
</batch>
"""

    def __init__(self, data):
        super(CreateStorage, self).__init__()
        self.__storage_code = data.get("erpWarehouseNo")
        self.__storage_name = data.get("name")
        self.__province = data.get("address").get("province")
        self.__city = data.get("address").get("city")
        self.__district = data.get("address").get("district")
        self.__addr = data.get("address").get("addr")
        self.__contact = data.get("address").get("name")
        self.__mobile = data.get("address").get("mobile")
        self.__remark = data.get("remark")

    def get_request_data(self):
        return self.request_data % (
            self.__storage_code, self.__storage_name, self.__province,
            self.__city, self.__district, self.__addr,
            self.__contact, self.__mobile, self.__remark,
        )

    def get_unique_define(self):
        return merge_str('create_storage', uuid.uuid4())

    def parse_response(self, response, task):
        # json 结果
        result = response.text
        return self.detect_xml_text(result)

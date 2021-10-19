import uuid
from copy import deepcopy

from hupun.page.base import *


class OrderSplitOp(Base):
    """
    在订单审核页面,操作订单的拆分
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
  "action": "resolve-data",
  "dataResolver": "saleInterceptor#unpack",
  "dataItems": [
    {
      "alias": "trade",
      "data": {
        "$isWrapper": true,
        "$dataType": "Trade",
        "data": %s
      },
      "refreshMode": "value",
      "autoResetEntityState": true
    },
    {
      "alias": "unpackList",
      "data": {
        "$isWrapper": true,
        "$dataType": "v:sale.approve$[Order]",
        "data": %s
      },
      "refreshMode": "value",
      "autoResetEntityState": true
    }
  ],
  "parameter": {
    "storageUid": "%s",
    "storageName": "%s",
    "remark": "%s",
    "memo": true
  },
  "context": {}
}
]]></request>
</batch>
"""

    def __init__(self, first_data, second_data, storage_uid, storage_name, remark):
        super(OrderSplitOp, self).__init__()
        self.__first_data = json.dumps(deepcopy(first_data))
        self.__second_data = json.dumps(deepcopy(second_data))
        self.__storage_uid = storage_uid
        self.__storage_name = storage_name
        self.__remark = remark

    def get_request_data(self):
        req_data = self.request_data % (
            self.__first_data, self.__second_data, self.__storage_uid, self.__storage_name, self.__remark
        )
        return req_data

    def get_unique_define(self):
        return merge_str('order_split_operate', uuid.uuid4())

    def parse_response(self, response, task):
        # json 结果
        result = response.text
        if 'exception' in result:
            err_msg = result.split('<exception', 1)[1].split('message:', 1)[1].split(',title', 1)[0].strip()
            return 'err_details:{}'.format(err_msg)
        result = self.detect_xml_text(response.text)
        return result

import copy
import json

from hupun.page.base import *


class CloseAudit(Base):
    """
    关闭审核标签的数据;
    关闭第二层的数据
    采购订单的关闭同步的断点名: beforeUpdate
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
    "action": "resolve-data",
    "dataResolver": "purchaseInterceptor#closePchsDetail",
    "dataItems": [
    {
        "alias": "bill",
        "data":
        {
            "$isWrapper": true,
            "$dataType": "v:purchase.bill$[purchaseBill]",
            "data": %s
        },
        "refreshMode": "value",
        "autoResetEntityState": true
    },
    {
        "alias": "detail",
        "data":
        {
            "$isWrapper": true,
            "$dataType": "v:purchase.bill$pchs_detail",
            "data": %s
        },
        "refreshMode": "state",
        "autoResetEntityState": true
    }],
    "parameter":
    {
        "remark": "%s"
    },
    "context": {}
 }
]]></request>
</batch>
"""

    def __init__(self, bill_data, bill_sku_data, remark=''):
        super(CloseAudit, self).__init__()
        self.__bill_data = copy.deepcopy(bill_data)
        self.__bill_sku_data = copy.deepcopy(bill_sku_data)
        self.__remark = remark

    def get_request_data(self):
        req_data = self.request_data % (json.dumps(self.__bill_data), json.dumps(self.__bill_sku_data), self.__remark)
        return req_data

    def get_unique_define(self):
        return merge_str('close_audit', self.__bill_data.get('bill_code', ''))

    def parse_response(self, response, task):
        # json 结果
        if '</exception>' in response.text:
            result = 'error:关闭采购订单失败'
            print(result)
            return result
        result = self.detect_xml_text(response.text)
        return_result = result['entityStates']
        return return_result

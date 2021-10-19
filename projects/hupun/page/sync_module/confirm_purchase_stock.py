import uuid

from hupun.page.base import *


class ConfirmPurBillStock(Base):
    """
    确认提交 采购入库单 的采购订单入库申请
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 %s
]]></request>
</batch>
"""

    def __init__(self, data):
        super(ConfirmPurBillStock, self).__init__()
        self.__data = data

    def get_request_data(self):
        data = self.request_data % json.dumps(self.__data)
        return data

    def get_unique_define(self):
        return merge_str('submit_purchase_bill_stock', uuid.uuid4())

    def parse_response(self, response, task):
        # json 结果
        result = self.detect_xml_text(response.text)['entityStates']
        return result

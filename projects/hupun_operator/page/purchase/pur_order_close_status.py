from hupun.page.base import *


class PurOrderCloseStatus(Base):
    """
    关闭采购跟单时刷新该采购跟单对应的采购订单数据
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
  "action": "load-data",
  "dataProvider": "purchaseInterceptor#queryPurchaseDetail",
  "supportsEntity": false,
  "parameter": "%s",
  "resultDataType": "v:purchase.bill$[pchs_detail]",
  "pageNo": 1,
  "context": {}
 }
]]></request>
</batch>
"""

    def __init__(self, bill_uid):
        super(PurOrderCloseStatus, self).__init__()
        self.__bill_uid = bill_uid

    def get_request_data(self):
        return self.request_data % self.__bill_uid

    def get_unique_define(self):
        return merge_str('purchase_order_close_status', self.__bill_uid)

    def parse_response(self, response, task):
        # json 结果
        result = self.detect_xml_text(response.text)
        return {
            'unique_name': 'purchase_order_close_status',
            'length': len(response.content),
            'response': result['data']
        }

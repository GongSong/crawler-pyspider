import copy

from hupun.page.base import *


class SubmitAudit(Base):
    """
    提交审核 标签的数据
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
   "action":"resolve-data",
   "dataResolver":"purchaseInterceptor#approveBills",
   "dataItems":[
     {
       "alias":"dsBill",
       "data":{
         "$isWrapper":true,
         "$dataType":"v:purchase.bill$[purchaseBill]",
         "data":[%s]
       },
       "refreshMode":"value",
       "autoResetEntityState":true
     }
   ],
   "parameter":{
     "pass":true,
     "content":"提交审核"
   },
   "context":{}
 }
]]></request>
</batch>
"""

    def __init__(self, bill_data):
        super(SubmitAudit, self).__init__()
        self.__data = copy.deepcopy(bill_data)
        self.__data['$dataType'] = "v:purchase.bill$purchaseBill"
        self.__data['$entityId'] = "0"

    def get_request_data(self):
        return self.request_data % json.dumps(self.__data)

    def get_unique_define(self):
        return merge_str('submit_audit', self._page)

    def parse_response(self, response, task):
        # json 结果
        result = self.detect_xml_text(response.text)
        return_result = result['returnValue']['data']
        return return_result

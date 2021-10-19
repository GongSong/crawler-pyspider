from hupun.page.base import *


class RequestToken(Base):
    """
    获取请求的token值
    """
    request_data = """
    <batch>
    <request type="json"><![CDATA[{"action":"remote-service","service":"mainService#getRequestToken","supportsEntity":true,"context":{},"loadedDataTypes":["Template","Combination","GoodsSpec","inventoryInOutReason","dtFractUnit","Region","PrintConfig","Catagory","Storage","appointmentDetail","dtSearch","Oper","appointmentBill","CombinationDetail","GoodsPermissions"]}]]></request>
    </batch>
    """

    def __init__(self):
        super(RequestToken, self).__init__()

    def get_request_data(self):
        return self.request_data

    def get_unique_define(self):
        now_timestamp = Date.now().millisecond()
        return merge_str('appointment_sku_info', now_timestamp)

    def parse_response(self, response, task):
        # json 结果
        print("token:  "+response.text)
        result = self.detect_xml_text(response.text)
        token = result.get("data", "")
        print(token)
        # 可能返回空值
        return token


if __name__ == '__main__':
    RequestToken().use_cookie_pool().get_result()


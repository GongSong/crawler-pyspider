from hupun.page.base import *


class QueryAppointmentDetail(Base):
    """
    查询 预约出库单 的商品详情
    """
    request_data = """
    <batch>
    <request type="json"><![CDATA[{"action":"load-data","dataProvider":"inventoryInterceptor#getAppointmentDetails","supportsEntity":true,"parameter":
    "%s","resultDataType":"v:inventory.outboundAppointment$[appointmentDetail]","context":{},
    "loadedDataTypes":["GoodsSpec","Region","Storage","Oper","appointmentBill","Catagory","dtFractUnit","dtSearch","Combination","appointmentDetail","PrintConfig","inventoryInOutReason","Template","CombinationDetail","GoodsPermissions"]}]]></request>
    </batch>
    """

    def __init__(self, erp_order_id):
        super(QueryAppointmentDetail, self).__init__()
        self.__order = erp_order_id

    def get_request_data(self):
        return self.request_data % (self.__order)

    def get_unique_define(self):
        return merge_str('query_appointment_outbound', self.__order)

    def parse_response(self, response, task):
        # 爬虫的抓取时间
        sync_time = Date.now().format_es_utc_with_tz()
        # json 结果
        print(response.text)
        result = self.detect_xml_text(response.text).get("data", {})
        return result


if __name__ == '__main__':
    QueryAppointmentDetail("69D6DCE35C743D79A279A9839F94D414").use_cookie_pool().get_result()

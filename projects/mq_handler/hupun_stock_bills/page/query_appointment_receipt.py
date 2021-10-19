from hupun.page.base import *


class QueryAppointmentReceipt(Base):
    """
    查询 预约入库单 信息
    """
    request_data = """
    <batch>
    <request type="json"><![CDATA[{"action":"load-data","dataProvider":"inventoryInterceptor#queryAppointmentBill","supportsEntity":true,"parameter":
        {"billType":1,"history":false,"billCode":"%s"},
        "resultDataType":"v:inventory.inboundAppointment$[appointmentBill]","pageSize":20,"pageNo":1,"context":{},
        "loadedDataTypes":["GoodsSpec","PrintConfig","Combination","dtSearch","Template","Storage","dtFractUnit","Catagory","Region","appointmentDetail","Oper","appointmentBill","inventoryInOutReason","GoodsPermissions","CombinationDetail"]}]]></request>
    </batch>
    """

    def __init__(self, erp_order_id):
        super(QueryAppointmentReceipt, self).__init__()
        self.__order = erp_order_id

    def get_request_data(self):
        return self.request_data % (self.__order)

    def get_unique_define(self):
        return merge_str('query_appointment_invoice', self.__order)

    def parse_response(self, response, task):
        # 爬虫的抓取时间
        sync_time = Date.now().format_es_utc_with_tz()
        # json 结果
        # print(response.text)
        result = self.detect_xml_text(response.text).get("data",{}).get("data", [])[0]
        print(result)
        return result


if __name__ == '__main__':
    QueryAppointmentReceipt("EO202007270002").use_cookie_pool().get_result()



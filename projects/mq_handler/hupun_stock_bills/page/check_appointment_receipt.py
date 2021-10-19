from hupun.page.base import *
from mq_handler.hupun_stock_bills.page.query_appointment_receipt import QueryAppointmentReceipt


class CheckAppointmentReceipt(Base):
    """
    审核 预约入库单
    """
    request_data = """
    <batch>
    <request type="json"><![CDATA[{"action":"resolve-data","dataResolver":"inventoryInOutboundInterceptor#approveAppointmentBill","dataItems":[{"alias":"dsBill","data":{"$isWrapper":true,"$dataType":"v:inventory.inboundAppointment$[appointmentBill]",
    "data":[
    %s
    ]},"refreshMode":"value","autoResetEntityState":true}],"parameter":{"remark":""},"context":{}}]]></request>
    </batch>
    """

    def __init__(self, erp_order_id):
        super(CheckAppointmentReceipt, self).__init__()
        self.__order = erp_order_id

    def get_request_data(self):
        data_list = QueryAppointmentReceipt(self.__order).use_cookie_pool().get_result()
        return self.request_data % (json.dumps(data_list))

    def get_unique_define(self):
        return merge_str('appointment_outbound', self.__order)

    def parse_response(self, response, task):
        # 爬虫的抓取时间
        sync_time = Date.now().format_es_utc_with_tz()
        # json 结果
        result = self.detect_xml_text(response.text)
        return True


if __name__ == '__main__':
    CheckAppointmentReceipt("EO202007270005").use_cookie_pool().get_result()

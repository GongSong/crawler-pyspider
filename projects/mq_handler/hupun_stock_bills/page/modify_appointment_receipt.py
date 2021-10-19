from hupun.page.base import *
from mq_handler.hupun_stock_bills.page.query_appointment_receipt import QueryAppointmentReceipt
from mq_handler.hupun_stock_bills.page.query_appointment_sku_info import AppointmentSkuInfo
from mq_handler.hupun_stock_bills.page.request_token import RequestToken


class ModifyAppointmentReceipt(Base):
    """
    修改 预约入库单
    """
    request_data = """
    <batch>
    <request type="json"><![CDATA[{"action":"resolve-data","dataResolver":"inventoryInOutboundInterceptor#saveAppointmentBill","dataItems":[{"alias":"dsBill","data":{"$isWrapper":true,"$dataType":"v:inventory.inboundAppointment$[appointmentBill]","data":{
    %s,
    "details":{"$isWrapper":true,"$dataType":"v:inventory.inboundAppointment$[appointmentDetail]",
    "data":%s
    },"$dataType":"appointmentBill","$state":2,"$entityId":"2628"
    }},"refreshMode":"value","autoResetEntityState":true}],
    "parameter":{"token":"%s"},"context":{}}]]></request>

    </batch>
    """

    def __init__(self, post_data):
        super(ModifyAppointmentReceipt, self).__init__()
        self.__storage_uid = "FBA807A72474376E8CFBBE9848F271B2"
        self.__receiver = post_data.get("receiver", "")
        self.__mobile = post_data.get("mobile", "")
        self.__address = post_data.get("address", "")
        self.__remark = post_data.get("remark", "")
        self.__sku_list = post_data.get("details", [])
        self.__order = post_data.get("order", "")

    def get_request_data(self):
        order_info = QueryAppointmentReceipt(self.__order).use_cookie_pool().get_result()
        order_info["address"] = self.__address
        order_info["mobile"] = self.__mobile
        order_info["receiver"] = self.__receiver
        order_info["remark"] = self.__remark
        order_info_str = json.dumps(order_info).replace("{", "").replace("}", "")

        new_detail_list = []
        for sku_info in self.__sku_list:
            detail = AppointmentSkuInfo(sku_info.get("spec_code"), sku_info.get("size"), self.__storage_uid).use_cookie_pool().get_result()
            new_detail_list.append(detail)
        new_detail_list_str = json.dumps(new_detail_list)
        token = RequestToken().use_cookie_pool().get_result()
        print(self.request_data % (order_info_str, new_detail_list_str, token))
        return self.request_data % (order_info_str, new_detail_list_str, token)

    def get_unique_define(self):
        return merge_str('modify_appointment_receipt', self.__remark, self.__storage_uid)

    def parse_response(self, response, task):
        # 爬虫的抓取时间
        sync_time = Date.now().format_es_utc_with_tz()
        # json 结果
        result = self.detect_xml_text(response.text)
        print(result)
        return result


if __name__ == '__main__':
    post_data = {
        'order': "EO202007270005",
        'address': "上海五角场二楼",
        'mobile': "15945678902",
        'receiver': "杨一里",
        'remark': "自动同步万里牛,配货单: PH202007020003测",
        'details': [
            {
                'size': 3,
                'spec_code': '2020D00018W302',
            },
            {
                'size': 3,
                'spec_code': '2020D00018W502',
            }
        ]
    }

    ModifyAppointmentReceipt(post_data).use_cookie_pool().get_result()




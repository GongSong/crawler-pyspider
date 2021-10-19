from hupun.page.base import *
from mq_handler.hupun_stock_bills.page.query_appointment_sku_info import AppointmentSkuInfo
from mq_handler.hupun_stock_bills.page.request_token import RequestToken


class AppointmentOutbound(Base):
    """
    创建 预约出库单
    """
    request_data = """
    <batch>
    <request type="json"><![CDATA[{"action":"resolve-data","dataResolver":"inventoryInOutboundInterceptor#saveAppointmentBill",
    "dataItems":[{"alias":"dsBill","data":{"$isWrapper":true,"$dataType":"v:inventory.outboundAppointment$[appointmentBill]",
    "data":{
    "bill_date":"%s",
    "operatorID":"475571006758820808","operatorName":"aipc1@yourdream.cc",
    "bill_type":2,"his":false,"status":0,"rowSelect":false,
    "storage_uid":"%s",
    "storage_name":"%s","details":{"$isWrapper":true,"$dataType":"v:inventory.outboundAppointment$[appointmentDetail]",
    "data": %s
    },
    "reasonName":"线下门店商品配送","reasonID":141,"deliveryName":"","deliveryID":"",
    "remark":"%s","address":"%s","receiver":"%s","mobile":"%s",
    "$dataType":"appointmentBill","$state":1,"$entityId":"1458"}},"refreshMode":"value","autoResetEntityState":true}],
    "parameter":{"token":"%s"},"context":{}}]]></request>
    </batch>
    """

    def __init__(self, post_data):
        super(AppointmentOutbound, self).__init__()
        self.__storage_uid = config.get('erp', 'storage_uid')
        self.__storage_name = config.get('erp', 'storage_name')
        self.__receiver = post_data.get("receiver", "")
        self.__mobile = post_data.get("mobile", "")
        self.__address = post_data.get("address", "")
        self.__remark = post_data.get("remark", "")
        self.__sku_list = post_data.get("details", [])

    def get_request_data(self):
        sync_time = Date.now().format_es_old_utc()
        token = RequestToken().use_cookie_pool().get_result()

        data_list = []
        for _sku_item in self.__sku_list:
            _sku = _sku_item.get("spec_code", '')
            _count = _sku_item.get("size", 0)
            _sku_info = AppointmentSkuInfo(_sku, _count, self.__storage_uid,).use_cookie_pool().get_result()
            data_list.append(_sku_info)
        return self.request_data % (sync_time, self.__storage_uid, self.__storage_name, json.dumps(data_list),
                                    self.__remark, self.__address, self.__receiver, self.__mobile, token)

    def get_unique_define(self):
        return merge_str('appointment_outbound', json.dumps(self.__sku_list), self.__storage_uid)

    def parse_response(self, response, task):
        # 爬虫的抓取时间
        sync_time = Date.now().format_es_utc_with_tz()
        # json 结果
        print(response.text)
        result = self.detect_xml_text(response.text)
        if result:
            return True
        else:
            return False


if __name__ == '__main__':
    post_data = {
        'address': "上海五角场",
        'mobile': "15945678901",
        'receiver': "杨十里",
        'remark': "自动同步万里牛,配货单: PH202007020002测",
        'details': [
            {
                'size': 20,
                'spec_code': '19490F0003R304',
            },
            {
                'size': 20,
                'spec_code': '1952D00050W172',
            }
        ]
    }
    AppointmentOutbound(post_data).use_cookie_pool().get_result()





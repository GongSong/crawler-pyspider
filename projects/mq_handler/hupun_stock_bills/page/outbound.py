from hupun.page.base import *
from mq_handler.hupun_stock_bills.page.query_appointment_detail import QueryAppointmentDetail
from mq_handler.hupun_stock_bills.page.query_appointment_outbound import QueryAppointmentOutbound
from mq_handler.hupun_stock_bills.page.request_token import RequestToken


class Outbound(Base):
    """
    创建 出库单
    """
    request_data = """
    <batch>
    <request type="json"><![CDATA[{"action":"resolve-data","dataResolver":"inventoryInterceptor#saveOtherInoutBill","dataItems":[{"alias":"dsBill",
    "data":{"$isWrapper":true,"$dataType":"v:inventory.outboundBill$[inOutboundBill]",
    "data":{"bill_date":"%s","operatorID":null,"operatorName":null,"bill_type":62,"his":false,"sumprice":0,"carriage":0,"price":0,"printTag":0,"rowSelect":false,
    "storage_uid":"%s","storage_name":"%s",
    "detail":{"$isWrapper":true,"$dataType":"v:inventory.outboundBill$[inOutboundDetail]",
    "data": %s
    },"pchs_bill_uid":"%s",
    "pchs_bill_code":"%s",
    "remark":"%s",
    "reasonID":%s,"reasonName":"%s","deliveryID":null,"deliveryName":null,"province":null,"city":null,"district":null,
    "address":"%s","mobile":"%s","tel":null,
    "receiver":"%s","$dataType":"inOutboundBill","$state":1,"$entityId":"2809"}},"refreshMode":"value","autoResetEntityState":true}],
    "parameter":{"token":"%s"},"context":{}}]]></request>
    </batch>
    """

    detail = """
    {"price":0,"pchs_price":0,"auto":false,"split":false,"unit_size":1,"goodsUid":"%s","goodsName":"%s","specUid":"%s","specCode":"%s","specName":null,"openSN":null,
        "nums":%s,"pchs_nums":1,"total_money":0,"unit":null,"unit_uid":null,"pchs_unit":null,"expiration":null,"shouldNums":%s,"pchs_detail_uid":"%s","$dataType":"inOutboundDetail","$state":1,"$entityId":"2874"}
    """

    def __init__(self, post_data):
        super(Outbound, self).__init__()
        self.__sku_list = post_data.get("details", [])
        self.__order = post_data.get("order", "")
        self.__receipt = post_data.get("outboundId", "")

    def get_request_data(self):
        sync_time = Date.now().format_es_old_utc()
        order_info = QueryAppointmentOutbound(self.__order).use_cookie_pool().get_result()
        storage_uid = order_info.get("storage_uid")
        storage_name = order_info.get("storage_name")
        pchs_bill_uid = order_info.get("bill_uid")
        pchs_bill_code = order_info.get("bill_code")
        remark = order_info.get("remark") + "，出库单：" + self.__receipt if self.__receipt else order_info.get("remark")
        reasonID = order_info.get("reasonID")
        reasonName = order_info.get("reasonName")
        address = order_info.get("address")
        mobile = order_info.get("mobile", "") if order_info.get("mobile", "") else ""
        receiver = order_info.get("receiver", "") if order_info.get("receiver", "") else ""

        # 将列表中的数据转为sku：count 的字典
        new_skus_dict = {}
        for _ in self.__sku_list:
            new_skus_dict[_.get("spec_code")] = _.get("size")

        goods_detail_list = QueryAppointmentDetail(pchs_bill_uid).use_cookie_pool().get_result()
        new_detail_list = []
        for goods_detail in goods_detail_list:
            goods_uid = goods_detail.get("goods_uid")
            goods_name = goods_detail.get("goods_name")
            spec_uid = goods_detail.get("spec_uid")
            spec_code = goods_detail.get("spec_code")
            should_nums = goods_detail.get("receive")
            pchs_detail_uid = goods_detail.get("detail_uid")
            count = new_skus_dict.get(spec_code, 0)
            if count == 0:
                continue
            print(self.detail % (goods_uid, goods_name, spec_uid, spec_code,count,should_nums,pchs_detail_uid))
            new_detail = json_loads(self.detail % (goods_uid, goods_name, spec_uid, spec_code, count, should_nums,pchs_detail_uid))
            new_detail_list.append(new_detail)
        new_detail_list_str = json.dumps(new_detail_list)
        token = RequestToken().use_cookie_pool().get_result()

        return self.request_data % (sync_time, storage_uid, storage_name, new_detail_list_str, pchs_bill_uid,
                                    pchs_bill_code, remark, reasonID, reasonName, address, mobile, receiver, token)

    def get_unique_define(self):
        return merge_str('add_outbound', self.__order)

    def parse_response(self, response, task):
        # 爬虫的抓取时间
        sync_time = Date.now().format_es_utc_with_tz()
        # json 结果
        print(response.text)
        result = self.detect_xml_text(response.text)
        return result


if __name__ == '__main__':
    post_data = {
        'order': "SO202009270002",
        'details': [
            {
                'size': 1,
                'spec_code': '1922A10009W703',
            },
            {
                'size': 0,
                'spec_code': '19160A0011W503',
            }
        ]
    }
    Outbound(post_data).use_cookie_pool().get_result()





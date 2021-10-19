import gevent.monkey
gevent.monkey.patch_ssl()
import requests
from mq_handler.hupun_stock_bills.page.check_appointment_outbound import CheckAppointmentOutbound
from mq_handler.hupun_stock_bills.model.distribute_order import DistributeOrder
from mq_handler.hupun_stock_bills.hupun_api.close_appointment_outbound import CloseAppointmentOutbound
from mq_handler.hupun_stock_bills.hupun_api.add_appointment_outbound import AppointmentOutbound
import json
from mq_handler.base import Base
from pyspider.helper.date import Date
import traceback
from pyspider.helper.retry import Retry
from alarm.page.ding_talk import DingTalk
from pyspider.config import config
from mq_handler.hupun_stock_bills.config import get_ding_token


class AddAppointmentOutbound(Base):
    '''
    创建 预约出库单
    '''

    def execute(self):
        print(Date.now().format(), '开始消费预约出库单')
        self.print_basic_info()
        data = self._data

        order = data.get("order", "")
        distribute_id = data.get("distribute_id", "")
        if not distribute_id:
            self.sync_errormsg_to_ai(distribute_id, "请求参数中无distribute_id，请确认")
            self.ding_talk_alarm('请求参数中无distribute_id，请确认参数:{}'.format(data))
            return
        # 如果传预约出库单号，则需要关闭该预约出库单。
        try:

            if order:
                result = CloseAppointmentOutbound().set_param('stock_request_code', order).get_result()
                close_res = json.loads(result).get("data", "")
                # 如果close_res不为True，则关闭失败，返回错误并钉钉报警。
                if not close_res:
                    erp_error_msg = json.loads(result).get("message", "")
                    sync_error_res = self.sync_errormsg_to_ai(distribute_id, erp_error_msg)
                    if not sync_error_res:
                        self.ding_talk_alarm("关闭原预约出库单失败，{}。且配货单：{}同步es错误原因失败".format(erp_error_msg, distribute_id))
                        print('同步es错误原因失败')

                    else:
                        print('=====关闭原预约出库单成功======')
                    return

            add_res = self.add_appointment_outbound(data)
            if add_res[0] is True:
                # 调拨单成功生成，保存该单,erp_sync_status=1为成功
                DistributeOrder.update(erp_invoice_order=add_res[1],erp_sync_status=1).where(
                    DistributeOrder.distribution_id == distribute_id).execute()
                sync_res = self.sync_to_ai(distribute_id,add_res)
                if not sync_res:
                    self.ding_talk_alarm("配货单：{}同步es失败".format(distribute_id))
                    print('同步es失败')
                    return
                else:
                    print('生成预约出库单成功')

            else:
                sync_error_res = self.sync_errormsg_to_ai(distribute_id, add_res[1])
                if not sync_error_res:
                    self.ding_talk_alarm("创建原预约出库单失败，{}。且配货单：{}同步es错误原因失败".format(add_res[1], distribute_id))
                    print('同步es错误原因失败')
                    return
                else:
                    self.ding_talk_alarm('配货单:{}生成预约出库单失败,{}'.format(distribute_id, add_res[1]))
                    print('配货单:{}生成预约出库单失败'.format(distribute_id))
                    return

            # 审核预约入库单
            check_appointment_res = self.check_appointment_outbound(add_res)
            if check_appointment_res[0] is True:
                print('=====审核成功，已完成预约出库单的生成======')
            else:
                self.ding_talk_alarm('配货单:{}审核预约出库单失败,{}'.format(distribute_id, check_appointment_res[1]))
                print('配货单:{}审核预约出库单失败'.format(distribute_id))
                return

        except:
            print(traceback.format_exc())
            self.sync_errormsg_to_ai(distribute_id, "未被捕捉到的生成预约出库单失败")
            self.ding_talk_alarm('配货单:{}未被捕捉到的生成预约出库单失败'.format(distribute_id))
            print('=====配货单:{}未正确生成预约出库单====='.format(distribute_id))


    @Retry.retry_parameter(3, sleep_time=50)
    def add_appointment_outbound(self, data):
        print(Date.now().format(), '开始创建预约出库单')
        try:
            res = AppointmentOutbound().set_param('bill', data).get_result()
            order_id = json.loads(res).get("data", "")
            if order_id:
                return True, order_id
            else:
                error_msg = '创建预约出库单失败，' + json.loads(res).get('message', '') \
                    if json.loads(res).get('message', '') else '创建预约出库单失败'
                return False, error_msg
        except Exception as e:
            print(traceback.format_exc())
            return False, '创建预约出库单发生异常错误'

    @Retry.retry_parameter(3, sleep_time=5)
    def check_appointment_outbound(self, add_res):
        try:
            CheckAppointmentOutbound(add_res[1]).use_cookie_pool().get_result()
            return True, True
        except Exception as e:
            print(traceback.format_exc())
            return False, '审核预约出库单发生异常错误'

    @staticmethod
    def ding_talk_alarm(error_msg, bill_code=''):
        token = get_ding_token()
        title = '生成预约出库单操作报警'
        bill_msg = '预约出库单：' + bill_code if bill_code else ''
        content = bill_msg + '生成预约出库单失败，原因：' + error_msg
        DingTalk(token, title, content).enqueue()

    def sync_to_ai(self, distribute_id, add_res):
        host = config.get("ai", "host")
        url = host + "/api/admin/data/searchHeadDeliveryOrder"
        body = {
            "id": distribute_id,
            "erpInvoiceOrder": add_res[1],
            "erpSyncStatus": "SUCCESS"
        }
        res = requests.post(url, json=body)
        if res.status_code == 200:
            return True
        else:
            return False

    def sync_errormsg_to_ai(self, distribute_id, error_msg):
        host = config.get("ai", "host")
        url = host + "/api/admin/data/searchHeadDeliveryOrder"
        body = {
            "id": distribute_id,
            "erpErrorMsg": error_msg
        }
        res = requests.post(url, json=body)
        if res.status_code == 200:
            return True
        else:
            return False

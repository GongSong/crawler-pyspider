import gevent.monkey
gevent.monkey.patch_ssl()
from mq_handler.hupun_stock_bills.hupun_api.close_appointment_outbound import CloseAppointmentOutbound
import json
from mq_handler.base import Base
from pyspider.helper.date import Date
import traceback
from alarm.page.ding_talk import DingTalk
from mq_handler.hupun_stock_bills.config import get_ding_token


class CloseAppOutboundMq(Base):
    '''
    关闭 预约出库单
    '''

    def execute(self):
        print(Date.now().format(), '开始消费关闭预约出库单')
        self.print_basic_info()
        data = self._data

        order = data.get("order", "")
        distribute_id = data.get("distribute_id", "")
        if not order:
            self.ding_talk_alarm('请求参数中无order，请确认参数:{}'.format(data))
            return
        try:
            result = CloseAppointmentOutbound().set_param('stock_request_code', order).get_result()
            close_res = json.loads(result).get("data", "")
            # 如果close_res不为True，则关闭失败，返回错误并钉钉报警。
            if not close_res:
                erp_error_msg = json.loads(result).get("message", "")
                self.ding_talk_alarm("关闭配货单{}的预约出库单失败，{}".format(erp_error_msg, distribute_id))
            else:
                print("====关闭预约出库单成功===")

        except:
            print(traceback.format_exc())
            self.ding_talk_alarm('配货单:{}未被捕捉到的关闭预约出库单失败'.format(distribute_id))
            print('=====配货单:{}未正确关闭预约出库单====='.format(distribute_id))


    @staticmethod
    def ding_talk_alarm(error_msg, bill_code=''):
        token = get_ding_token()
        title = '关闭预约出库单操作报警'
        bill_msg = '预约出库单：' + bill_code if bill_code else ''
        content = bill_msg + error_msg
        DingTalk(token, title, content).enqueue()


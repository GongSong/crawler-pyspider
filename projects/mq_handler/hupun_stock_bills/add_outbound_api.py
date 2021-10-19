import gevent.monkey
gevent.monkey.patch_ssl()
from mq_handler.hupun_stock_bills.hupun_api.add_outbound_order import OutboundOrder
import json
from mq_handler.base import Base
from pyspider.helper.date import Date
import traceback
from pyspider.helper.retry import Retry
from alarm.page.ding_talk import DingTalk
from mq_handler.hupun_stock_bills.config import get_ding_token


class AddOutboundApi(Base):
    '''
    创建 预约出库单
    '''

    def execute(self):
        print('开始创建出库单')
        self.print_basic_info()
        data = self._data

        try:
            add_res = self.add_outbound(data)
            if add_res[0] is True:
                # 调拨单成功生成，保存该单
                print('=====已完成出库单的生成======')

            else:
                self.ding_talk_alarm(add_res[1])
                print('生成出库单失败')
        except:
            print(traceback.format_exc())
            self.ding_talk_alarm('未被捕捉到的生成出库单失败')
            print('=====未正确生成出库单=====')

    @Retry.retry_parameter(2, sleep_time=5)
    def add_outbound(self, data):
        print(Date.now().format(), '开始调创建出库单api')
        try:
            self._data = data
            res = OutboundOrder().set_param('bill', data).get_result()
            order_id = json.loads(res).get("data", "")
            if order_id:
                return True, order_id
            else:
                error_msg = '调用API增加出库单失败，' + json.loads(res).get('message', '') \
                    if json.loads(res).get('message', '') else '调用API增加出库单失败'
                return 'other', error_msg
        except Exception as e:
            print(traceback.format_exc())
            return False, '调用api发生异常错误'

    @staticmethod
    def ding_talk_alarm(error_msg, bill_code=''):
        token = get_ding_token()
        title = '生成出库单操作报警'
        bill_msg = '出库单：' + bill_code if bill_code else ''
        content = bill_msg + '生成出库单失败，原因：' + error_msg
        DingTalk(token, title, content).enqueue()


import gevent.monkey
gevent.monkey.patch_ssl()
from mq_handler.hupun_stock_bills.page.receipt import Receipt
import json
from mq_handler.base import Base
from pyspider.helper.date import Date
import traceback
from pyspider.helper.retry import Retry
from alarm.page.ding_talk import DingTalk
from mq_handler.hupun_stock_bills.config import get_ding_token


class AddReceipt(Base):
    '''
    创建 出入库单
    '''

    def execute(self):
        print(Date.now().format(), '开始创建入库单')
        self.print_basic_info()
        data = self._data

        order = data.get("order", "")
        if not order:
            self.ding_talk_alarm('参数order未传递，请确认参数:{}'.format(data))
            return
        try:
            add_res = self.add_receipt(data, order)
            if add_res[0] is True:
                # 调拨单成功生成，保存该单
                print('=====已完成入库单的生成======')

            else:
                self.ding_talk_alarm("预约入库单:{}生成万里牛入库单失败,{}".format(order, add_res[1]))
                print("预约入库单:{}生成入库单失败,{}".format(order, add_res[1]))
        except:
            print(traceback.format_exc())
            self.ding_talk_alarm('预约入库单:{},未被捕捉到的生成入库单失败'.format(order))
            print('=====预约入库单:{},未被捕捉到的生成出库单失败====='.format(order))

    @Retry.retry_parameter(3, sleep_time=50, rate=1)
    def add_receipt(self, data, order):
        print(Date.now().format(), '预约入库单:{}开始入库单'.format(order))
        try:
            res = Receipt(data).use_cookie_pool().get_result()

            if res:
                return True, res
            else:
                error_msg = '生成入库单失败，' + json.loads(res).get('message', '') \
                    if json.loads(res).get('message', '') else '生成入库单失败'
                return False, error_msg
        except Exception as e:
            print(traceback.format_exc())
            return False, '由于万里牛账户cookie失效，多次重试生成入库单失败，可以等一下继续尝试'

    @staticmethod
    def ding_talk_alarm(error_msg):
        token = get_ding_token()
        title = '生成入库单操作报警'
        content = error_msg
        DingTalk(token, title, content).enqueue()

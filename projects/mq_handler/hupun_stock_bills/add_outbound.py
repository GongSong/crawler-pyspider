import gevent.monkey
gevent.monkey.patch_ssl()
from mq_handler.hupun_stock_bills.model.erp_receipt_info import ErpReceiptInfo
from mq_handler.hupun_stock_bills.page.query_outbound import QueryOutbound
from mq_handler.hupun_stock_bills.page.outbound import Outbound
import json
from mq_handler.base import Base
from pyspider.helper.date import Date
import traceback
from pyspider.helper.retry import Retry
from alarm.page.ding_talk import DingTalk
from mq_handler.hupun_stock_bills.config import get_ding_token


class AddOutbound(Base):
    '''
    创建 出库单
    '''

    def execute(self):
        print(Date.now().format(), '开始创建出库单')
        self.print_basic_info()
        data = self._data

        order = data.get("order", "")
        receipt_id = data.get("receiptId", "")
        outbound = data.get("outboundId", "")
        if not order or not receipt_id:
            self.ding_talk_alarm('参数order或receipt_id为空，请确认参数:{}'.format(data))
            return

        try:
            add_res = self.add_outbound(data, order)
            if not add_res[0]:
                # 出库单生成失败，退出
                self.ding_talk_alarm("预约出库单:{},出库单{}生成万里牛出库单失败,{}".format(order, outbound, add_res[1]))
                print("预约出库单:{}生成出库单失败,{}".format(order, add_res[1]))
                return

            query_res = self.query_outbound(outbound)
            if not query_res[0]:
                # 查询出库单号失败
                self.ding_talk_alarm("预约出库单:{},出库单{}生成万里牛出库单失败, 未查询到出库单号".format(order, outbound))
                print("预约出库单:{}生成出库单失败,{}".format(order, add_res[1]))
                return

            create_time = Date.now().timestamp()
            ErpReceiptInfo.insert(receipt_id=receipt_id,
                                  erp_outbound=query_res[1],
                                  outbound=outbound,
                                  create_time=create_time).execute()

            self.sync_ai_mq(receipt_id)
            print('=====已完成出库单的生成======')

        except Exception as e:
            print(traceback.format_exc())
            self.ding_talk_alarm('预约出库单:{},出库单{},未被捕捉到的生成出库单失败,{}'.format(order, outbound, e))
            print('=====预约出库单:{},出库单{},未被捕捉到的生成出库单失败====='.format(order, outbound))

    @Retry.retry_parameter(4, sleep_time=10)
    def add_outbound(self, data, order):
        print(Date.now().format(), '预约出库单:{}开始创建出库单'.format(order))
        try:
            res = Outbound(data).use_cookie_pool().get_result()

            if res:
                return True, res
            else:
                error_msg = '生成出库单失败，' + json.loads(res).get('message', '') \
                    if json.loads(res).get('message', '') else '生成出库单失败'
                return False, error_msg
        except Exception as e:
            print(traceback.format_exc())
            return False, '生成出库单发生异常错误'

    @Retry.retry_parameter(4, sleep_time=10)
    def query_outbound(self, outbound):
        try:
            res = QueryOutbound(outbound).set_start_time(Date.now().plus_days(-120).format()).use_cookie_pool().get_result()

            if res:
                return True, res
            else:
                error_msg = '查询出库单失败，' + json.loads(res).get('message', '') \
                    if json.loads(res).get('message', '') else '查询出库单失败'
                return False, error_msg
        except Exception as e:
            print(traceback.format_exc())
            return False, '查询出库单发生异常'

    @staticmethod
    def ding_talk_alarm(error_msg):
        token = get_ding_token()
        title = '生成出库单操作报警'
        content = error_msg
        DingTalk(token, title, content).enqueue()

    def sync_ai_mq(self, receipt_id):
        from pyspider.libs.mq import MQ
        tag = "GraphqlIndex"
        index = "ReceiveOrder"
        ids = [receipt_id]
        data = {
            "index": index,
            "ids": ids
        }
        data_id = '118'
        action = "create"
        MQ().publish_message(tag, data, data_id, Date.now().timestamp(), action)

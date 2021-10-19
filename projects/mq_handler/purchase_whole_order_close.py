import json
import traceback
from alarm.config import HUPUN_SYNC_ABNORMAL_ROBOT
from alarm.helper import Helper
from alarm.page.ding_talk import DingTalk
from cookie.config import ROBOT_TOKEN
from hupun.config import HUPUN_SEARCH_DAYS
from hupun.page.purchase_order_query_result import POrderQueResult
from hupun_api.page.purchase_order_close import PurchaseOrderClose
from mq_handler.base import Base
from pyspider.helper.date import Date
from pyspider.helper.email import EmailSender


class PurWholeOrderClose(Base):
    """
    采购单整单关闭
    """
    # 采购订单不能关闭的状态值
    PUR_COMPLETE = 3  # 已完成
    PUR_CLOSED = 4  # 已关闭
    # 采购订单可以关闭的状态值
    NOT_ARRIVED = 1  # 未到货
    PARTIAL_ARRIVED = 2  # 部分到货
    # 关闭备注
    close_remark = 'spider-whole-close-mark'

    def execute(self):
        print('整单关闭采购订单')
        self.print_basic_info()

        # 获取数据
        bill_code = self._data.get('erpPurchaseNo')  # 万里牛采购单号
        form_id = self._data.get('formId')
        purchase_id = self._data.get('purchaseId')  # tg的采购单ID
        # 异常数据
        error_msg_str = ''
        # 通用返回数据
        data = {
            'formId': form_id,
            'erpPurchaseNo': bill_code,
            'purchaseId': purchase_id,
        }

        def send_success_msg(success_bill_uid):
            """
            发送成功之后的数据
            :param success_bill_uid:
            :return:
            """
            self.send_call_back_msg(status=0, return_data=data)

            # 更新已关闭采购订单的数据
            print('更新的采购订单: {}'.format(success_bill_uid))
            # PurchaseOrderGoods(success_bill_uid) \
            #     .set_priority(PurchaseOrderGoods.CONST_PRIORITY_BUNDLED) \
            #     .use_cookie_pool() \
            #     .enqueue()

        try:
            print('同步获取采购订单: {}的数据'.format(bill_code))
            pur_order_query_obj = POrderQueResult(bill_code) \
                .set_start_time(Date.now().plus_days(-HUPUN_SEARCH_DAYS).format()) \
                .set_cookie_position(1)
                # .use_cookie_pool()
            status, result = Helper().get_sync_result(pur_order_query_obj)
            if status == 1:
                raise Exception(result)

            if result:
                result = result[0]
                bill_uid = result.get('bill_uid', '')

                # 判断采购单是否可以被关闭
                bill_status = int(result.get('status', 0))
                if bill_status == self.NOT_ARRIVED or bill_status == self.PARTIAL_ARRIVED:
                    print("可以整单关闭采购单:{}".format(bill_code))
                    close_msg = self.close_purchase_bill(bill_code=bill_code, close_remark=self.close_remark)
                    if close_msg:
                        error_msg_str = '整单关闭采购单:{}失败,原因: {};'.format(bill_code, close_msg)
                        print(error_msg_str)
                    else:
                        print('整单关闭采购单:{}成功'.format(bill_code))

                print('error_msg_str: {}'.format(error_msg_str))
                if error_msg_str:
                    self.send_call_back_msg(error_msg_str, status=1, return_data=data)
                else:
                    # 发送成功关闭的消息
                    send_success_msg(bill_uid)
            else:
                # 没有数据，报警
                error_msg_str = '没有获取到被整关闭的采购单: {}的信息'.format(bill_code)
                print(error_msg_str)
                self.send_call_back_msg(error_msg_str, status=1, return_data=data)
        except Exception as e:
            print('------')
            print(traceback.format_exc())
            print('------')
            error_msg_str = '关闭采购订单时发生未知异常: {}; erpPurchaseNo:{}'.format(e, bill_code)
            print(error_msg_str)
            self.send_call_back_msg(error_msg_str, status=1, return_data=data)
            raise e

    def close_purchase_bill(self, bill_code='', close_remark='', retry=3):
        """
        根据采购单整单关闭采购订单;
        :param bill_code:
        :param close_remark: 关闭备注
        :param retry:
        :return:
        """
        try:
            close_obj = PurchaseOrderClose().set_param('bill_code', bill_code).set_param('close_remark', close_remark)
            close_status, close_result = Helper().get_sync_result(close_obj)
            result = json.loads(close_result)

            code = result.get('code')
            if code != 0:
                if retry > 0:
                    return self.close_purchase_bill(bill_code, close_remark, retry - 1)
                else:
                    # 发送整单关闭采购单失败的钉钉通知
                    title = '整单关闭采购单失败报警'
                    text = '整单关闭采购单失败了: {} 次, 需要手动去万里牛关闭异常订单: {}'.format(retry, bill_code)
                    DingTalk(ROBOT_TOKEN, title, text).enqueue()
            return result.get('message')
        except Exception as e:
            print('--------error traceback--------')
            print(traceback.format_exc())
            print('整单关闭采购单 error: {}'.format(e))
            if retry > 0:
                return self.close_purchase_bill(bill_code, close_remark, retry - 1)
            else:
                # 发送关闭采购单失败的钉钉通知
                title = '整单关闭采购单失败报警'
                text = '整单关闭采购单失败了: {} 次, 需要手动去万里牛关闭异常订单: {}'.format(retry, bill_code)
                DingTalk(ROBOT_TOKEN, title, text).enqueue()
                return 'error关闭采购单失败，重试次数: {}'.format(retry)

    def send_call_back_msg(self, err_msg='', status=1, return_data=''):
        """
        发送返回的消息数据
        :return:
        """
        return_msg = {
            "code": status,  # 0：成功 1：失败
            "errMsg": err_msg,  # 如果code为1，请将失败的具体原因返回
            "data": return_data
        }
        # 发送失败的消息
        if status != 0 and Helper.in_project_env():
            # 发送失败的消息
            title = '万里牛采购单整单关闭失败'
            ding_msg = '万里牛采购单整单关闭失败失败原因: {}, 天鸽采购单号: {}, 万里牛采购单号: {}'.format(
                err_msg, self._data.get('purchaseId'), return_data.get('erpPurchaseNo'))
            DingTalk(HUPUN_SYNC_ABNORMAL_ROBOT, title, ding_msg).enqueue()
            # 同时发送邮件通知
            if self._data.get('email'):
                EmailSender() \
                    .set_receiver(self._data.get('email')) \
                    .set_mail_title(title) \
                    .set_mail_content(ding_msg) \
                    .send_email()
        print('发送返回的消息数据: {}'.format(return_msg))
        from mq_handler import CONST_ACTION_UPDATE
        from pyspider.libs.mq import MQ
        from mq_handler import CONST_MESSAGE_TAG_PURCHARSE_WHOLE_CLOSE_RE
        msg_tag = CONST_MESSAGE_TAG_PURCHARSE_WHOLE_CLOSE_RE
        return_date = Date.now().format()
        MQ().publish_message(msg_tag, return_msg, self._data_id, return_date, CONST_ACTION_UPDATE)

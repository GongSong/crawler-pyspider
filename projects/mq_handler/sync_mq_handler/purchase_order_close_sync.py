import json
import traceback
from alarm.config import HUPUN_SYNC_ABNORMAL_ROBOT
from alarm.helper import Helper
from alarm.page.ding_talk import DingTalk
from cookie.config import ROBOT_TOKEN
from hupun.config import HUPUN_SEARCH_DAYS
from hupun.page.purchase_order_goods import PurchaseOrderGoods
from hupun.page.purchase_order_query_result import POrderQueResult
from hupun_api.page.purchase_order_close import PurchaseOrderClose
from pyspider.helper.date import Date
from pyspider.core.model.storage import default_storage_redis
from pyspider.helper.email import EmailSender
from pyspider.helper.string import merge_str


class PurOrderSyncClose:
    """
    整单关闭采购单-同步操作(采购单里的商品)
    """
    ClOSE_FAIL_TIMES_KEY = 'hupun_purchase_close_fails'  # redis中关闭订单失败次数的key
    # 采购订单不能关闭的状态值
    PUR_COMPLETE = 3  # 已完成
    PUR_CLOSED = 4  # 已关闭
    # 采购跟单的状态值
    NOT_ARRIVED = 0  # 未到货
    PARTIAL_ARRIVED = 1  # 部分到货
    FULL_ARRIVED = 2  # 全部到货, 不能操作关闭
    CLOSED = 3  # 已关闭, 不能操作关闭
    # 关闭备注
    close_remark = 'spider-close-mark'

    def __init__(self, data):
        self.form_id = data.get('formId')
        # tg的采购单ID
        self.purchase_id = data.get('purchaseId')
        # 万里牛采购单号
        self.bill_code = data.get('erpPurchaseNo')
        # 发生错误后被通知到的邮件地址
        self.email = data.get('email')
        # 是否成功整单关闭采购单
        self.is_close_success = False

        self.data_id = data.get('dataId')
        self.message_id = data.get('message_id')
        self.publish_time = data.get('publish_time')
        self.publish_service = data.get('publish_service')
        self.action = data.get('action')

    def print_basic_info(self):
        """
        打印接受到的基本数据
        :return:
        """
        print("messageId:", self.message_id)
        print("dataId:", self.data_id)
        print("publishTime:", Date(self.publish_time).format())
        print("publishService:", self.publish_service)
        print("action:", self.action)
        print("now:", Date.now().format())
        print("formId:", self.form_id)
        print("purchaseId:", self.purchase_id)
        print("erpPurchaseNo:", self.bill_code)
        print("email:", self.email)

    def execute(self):
        print('关闭采购订单-同步')
        self.print_basic_info()

        # 获取数据
        fail_times = 0
        bill_code = self.bill_code
        error_msg_str = ''
        # 采购单是否是已经关闭了，已完成和已关闭的状态是不能被关闭的状态, 默认未关闭
        purchase_bill_status = False

        def send_success_msg(bill_uid):
            """
            发送成功之后的数据
            :param bill_uid:
            :return:
            """
            re_data = {
                'formId': self.form_id,
                'erpPurchaseNo': bill_code,
                'purchaseId': self.purchase_id,
            }
            self.send_call_back_msg(error_msg_str, data_id=self.data_id, status=0, return_data=re_data)
            # 当正常关闭采购订单后，将连续失败次数重置为0
            default_storage_redis.set(self.ClOSE_FAIL_TIMES_KEY, 0)

            # 更新已关闭采购订单的数据
            print('更新的采购订单: {}'.format(bill_uid))
            PurchaseOrderGoods(bill_uid) \
                .set_priority(PurchaseOrderGoods.CONST_PRIORITY_BUNDLED) \
                .use_cookie_pool() \
                .enqueue()
            self.is_close_success = True

        print('开始获取数据')

        try:
            # 从redis获取的之前连续失败的次数，如大于等于9则告警并将该值重新置零。
            fail_times = default_storage_redis.get(self.ClOSE_FAIL_TIMES_KEY)
            if not fail_times:
                print('错误，未获取到fail_times的值！')
                default_storage_redis.set(self.ClOSE_FAIL_TIMES_KEY, 0)
                fail_times = 0
            else:
                fail_times = int(fail_times)
            if fail_times >= 9:
                ding_msg = '已连续10次未正确关闭erp，请及时上线检查。'
                print(ding_msg)
                title = '关闭采购订单的程序警告'
                DingTalk(ROBOT_TOKEN, title, ding_msg).enqueue()
                fail_times = 0
                default_storage_redis.set(self.ClOSE_FAIL_TIMES_KEY, 0)

            print('整单关闭采购订单, 同步获取采购单: {}的数据'.format(bill_code))
            pur_order_query_obj = POrderQueResult(bill_code) \
                .set_start_time(Date.now().plus_days(-HUPUN_SEARCH_DAYS).format()) \
                .use_cookie_pool()
            status, result = Helper().get_sync_result(pur_order_query_obj)
            if status == 1:
                raise Exception(result)

            if result:
                result = result[0]
                bill_uid = result.get('bill_uid', '')

                # 判断采购单是否已经被关闭,是则跳过
                if int(result.get('status', 0)) == self.PUR_CLOSED or int(result.get('status', 0)) == self.PUR_COMPLETE:
                    print('采购单:{}已经被关闭,设置该采购单的关闭状态'.format(bill_code))
                    purchase_bill_status = True

                # 判断是否可以关闭采购单
                if not purchase_bill_status:
                    print("可以整单关闭采购单:{}".format(bill_code))
                    close_msg = self.close_purchase_bill(bill_code=bill_code, close_remark=self.close_remark)
                    if close_msg:
                        err_msg = '整单关闭采购单:{}失败,原因: {};'.format(bill_code, close_msg)
                        error_msg_str += err_msg
                        print(error_msg_str)
                    else:
                        print('整单关闭采购单:{}成功'.format(bill_code))

                data = {
                    'formId': self.form_id,
                    'erpPurchaseNo': bill_code,
                    'purchaseId': self.purchase_id,
                }
                print('error_msg_str: {}'.format(error_msg_str))
                if error_msg_str:
                    self.send_call_back_msg(error_msg_str, data_id=self.data_id, return_data=data)
                    default_storage_redis.set(self.ClOSE_FAIL_TIMES_KEY, fail_times + 1)
                else:
                    # 发送成功关闭的消息
                    send_success_msg(bill_uid)
            else:
                # 没有数据，报警
                err_msg = '整单关闭采购订单,没有获取到被关闭的采购单: {} 的信息'.format(bill_code)
                print(err_msg)
                error_msg_str += ';{}'.format(err_msg)
                print(error_msg_str)
                data = {
                    'formId': self.form_id,
                    'erpPurchaseNo': bill_code,
                    'purchaseId': self.purchase_id,
                }
                default_storage_redis.set(self.ClOSE_FAIL_TIMES_KEY, fail_times + 1)
                self.send_call_back_msg(error_msg_str, data_id=self.data_id, return_data=data)
        except Exception as e:
            print('----')
            print(traceback.format_exc())
            print('------')
            err_msg = '关闭采购订单时发生未知异常: {}; erpPurchaseNo:{}'.format(e, self.bill_code)
            print(err_msg)
            error_msg_str += ';{}'.format(err_msg)
            print(error_msg_str)
            data = {
                'formId': self.form_id,
                'erpPurchaseNo': bill_code,
                'purchaseId': self.purchase_id,
            }
            self.send_call_back_msg(error_msg_str, data_id=self.data_id, return_data=data)
            default_storage_redis.set(self.ClOSE_FAIL_TIMES_KEY, fail_times + 1)
        return self.is_close_success

    def close_purchase_bill(self, bill_code='', level=1, bill_data='', bill_sku_data='', close_remark='', retry=3):
        """
        根据采购单据编码关闭采购订单;
        这个关闭的是第一层的采购订单（第一层指的是直接查询万里牛返回的面板信息）
        :param bill_code:
        :param level: 1，整单关闭； 2，部分关闭采购单里的商品
        :param bill_data:
        :param bill_sku_data:
        :param close_remark: 关闭备注
        :param retry: 重试次数
        :return:
        """
        try:
            result = PurchaseOrderClose() \
                .set_param('bill_code', bill_code) \
                .set_param('close_remark', close_remark) \
                .get_result()
            result = json.loads(result)
            code = result.get('code')
            if code != 0:
                if retry > 0:
                    return self.close_purchase_bill(bill_code, level, bill_data, bill_sku_data, close_remark, retry - 1)
                else:
                    # 发送关闭采购单失败的钉钉通知
                    title = '关闭采购单失败报警'
                    text = '关闭采购单失败了: {} 次, 需要手动去万里牛关闭异常订单: {}'.format(retry, bill_code)
                    DingTalk(ROBOT_TOKEN, title, text).enqueue()
            return result.get('message')
        except Exception as e:
            print('--------error traceback--------')
            print(traceback.format_exc())
            print('close_purchase_bill close bill error: {}'.format(e))
            if retry > 0:
                return self.close_purchase_bill(bill_code, level, bill_data, bill_sku_data, close_remark, retry - 1)
            else:
                # 发送关闭采购单失败的钉钉通知
                title = '关闭采购单失败报警'
                text = '关闭采购单失败了: {} 次, 需要手动去万里牛关闭异常订单: {}'.format(retry, bill_code)
                DingTalk(ROBOT_TOKEN, title, text).enqueue()
                return 'error关闭采购单失败，重试次数: {}'.format(retry)

    def send_call_back_msg(self, err_msg='', data_id='', status=1, return_data=''):
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
            title = '万里牛采购跟单关闭失败'
            ding_msg = '万里牛采购跟单关闭失败原因: {}, 天鸽采购跟单号: {}, 万里牛采购单号: {}'.format(
                err_msg, merge_str('CGGD', self.form_id, dividing=''), return_data.get('erpPurchaseNo'))
            DingTalk(HUPUN_SYNC_ABNORMAL_ROBOT, title, ding_msg).enqueue()
            # 同时发送邮件通知
            if self.email:
                EmailSender() \
                    .set_receiver(self.email) \
                    .set_mail_title(title) \
                    .set_mail_content(ding_msg) \
                    .send_email()
        print('发送返回的消息数据: {}'.format(return_msg))
        from mq_handler import CONST_MESSAGE_TAG_PURCHARSE_CLOSE_RE
        from mq_handler import CONST_ACTION_UPDATE
        from pyspider.libs.mq import MQ
        msg_tag = CONST_MESSAGE_TAG_PURCHARSE_CLOSE_RE
        return_date = Date.now().format()
        MQ().publish_message(msg_tag, return_msg, data_id, return_date, CONST_ACTION_UPDATE)

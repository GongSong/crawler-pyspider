import json
import traceback
from copy import deepcopy
from alarm.config import HUPUN_SYNC_ABNORMAL_ROBOT
from alarm.helper import Helper
from alarm.page.ding_talk import DingTalk
from cookie.config import ROBOT_TOKEN
from hupun.config import HUPUN_SEARCH_DAYS
from hupun.model.es.purchase_order_close_msg import PurOrderCloseMsg
from hupun_slow_crawl.model.es.supplier import Supplier
from hupun.page.purchase_order_goods import PurchaseOrderGoods
from hupun.page.purchase_order_goods_result import PurOrderGoodsResult
from hupun.page.purchase_order_query_result import POrderQueResult
from hupun_api.page.purchase_order_close import PurchaseOrderClose
from hupun_operator.page.purchase.close_audit import CloseAudit
from mq_handler.base import Base
from pyspider.helper.date import Date
from pyspider.core.model.storage import default_storage_redis
from pyspider.helper.email import EmailSender
from pyspider.helper.string import merge_str


class PurOrderClose(Base):
    """
    关闭采购跟单(采购单里的商品)
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

    def execute(self):
        print('关闭采购订单')
        self.print_basic_info()

        # 获取数据
        bill_code = self._data.get('erpPurchaseNo')
        data_list = self._data.get('list')
        form_id = self._data.get('formId')
        error_msg_str = ''
        sku_barcode_list = set()  # 失败的sku合集
        sku_barcode_success_list = set()  # 成功的sku合集
        sku_invalid_close_list = [self.FULL_ARRIVED, self.CLOSED]
        purchase_bill_status = False  # 在外部的是否是能够被关闭的采购单的状态,已完成和已关闭的状态是不能被关闭的状态,默认未关闭
        compared_pur_sku_status = False  # 判断采购跟单是否有对不上的数据,有则为True,默认是正常的,False,对得上

        def send_success_msg(bill_uid):
            """
            发送成功之后的数据
            :param bill_uid:
            :return:
            """
            re_data = {
                'formId': self._data.get('formId'),
                'bill_code': bill_code,
                'skuBarcodeFailed': list(sku_barcode_list),
                'skuBarcodeSuccessed': list(sku_barcode_success_list),
            }
            self.send_call_back_msg(error_msg_str, data_id=self._data_id, status=0, return_data=re_data)
            # 当正常关闭采购订单后，将连续失败次数重置为0
            default_storage_redis.set(self.ClOSE_FAIL_TIMES_KEY, 0)

            # 保存发过来的原始数据
            save_list = list()
            for _data in data_list:
                save_data = dict()
                save_data['sku_barcode'] = _data.get('skuBarcode')
                save_data['form_id'] = form_id
                save_data['bill_code'] = bill_code
                save_data['supplier_code'] = _data.get('supplierCode')
                save_data['purchase_count'] = _data.get('purchaseCount')
                save_data['arrive_count'] = _data.get('arriveCount')
                save_data['close_count'] = _data.get('closeCount')
                save_data['check_status'] = False
                save_list.append(save_data)
            PurOrderCloseMsg().update(save_list, async=True)

            # 更新已关闭采购订单的数据
            print('更新的采购订单: {}'.format(bill_uid))
            PurchaseOrderGoods(bill_uid) \
                .set_priority(PurchaseOrderGoods.CONST_PRIORITY_BUNDLED) \
                .use_cookie_pool() \
                .enqueue()

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

            data_length = len(data_list)

            for _d in data_list:
                sku_barcode_list.add(_d['skuBarcode'])

            print('同步获取采购单: {}的数据'.format(bill_code))
            pur_order_query_obj = POrderQueResult(bill_code) \
                .set_start_time(Date.now().plus_days(-HUPUN_SEARCH_DAYS).format()) \
                .use_cookie_pool()
            status, result = Helper().get_sync_result(pur_order_query_obj)
            if status == 1:
                raise Exception(result)

            if result:
                result = result[0]
                bill_uid = result.get('bill_uid', '')

                sku_result = PurOrderGoodsResult(bill_uid) \
                    .use_cookie_pool() \
                    .get_result(retry_limit=3, retry_interval=30)

                if not sku_result:
                    err_msg = '采购单:{} 没有抓取到sku级别的采购跟单'.format(bill_code)
                    print(err_msg)
                    error_msg_str += ';{}'.format(err_msg)
                    print(error_msg_str)
                    data = {
                        'formId': self._data.get('formId'),
                        'bill_code': bill_code,
                        'skuBarcodeFailed': list(sku_barcode_list),
                        'skuBarcodeSuccessed': list(sku_barcode_success_list),
                    }
                    default_storage_redis.set(self.ClOSE_FAIL_TIMES_KEY, fail_times + 1)
                    return self.send_call_back_msg(error_msg_str, data_id=self._data_id, return_data=data)

                # 有数据，获取采购单的sku级别的数据
                print('有数据，获取采购单的sku级别的数据')
                if len(sku_result) < data_length:
                    err_msg = '关闭采购单: {} 失败, 因为传入到采购跟单数量是: {} ,大于爬虫抓取的数量: {}'.format(
                        bill_code, data_length, len(sku_result))
                    print(err_msg)
                    error_msg_str += ';{}'.format(err_msg)
                    print(error_msg_str)
                    data = {
                        'formId': self._data.get('formId'),
                        'bill_code': bill_code,
                        'skuBarcodeFailed': list(sku_barcode_list),
                        'skuBarcodeSuccessed': list(sku_barcode_success_list),
                    }
                    default_storage_redis.set(self.ClOSE_FAIL_TIMES_KEY, fail_times + 1)
                    return self.send_call_back_msg(error_msg_str, data_id=self._data_id, return_data=data)

                # 判断采购单是否已经被关闭,是则跳过
                if int(result.get('status', 0)) == self.PUR_CLOSED or int(result.get('status', 0)) == self.PUR_COMPLETE:
                    print('采购单:{}已经被关闭,设置该采购单的关闭状态'.format(bill_code))
                    purchase_bill_status = True

                # 判断需要关闭的采购单是否满足 (整单关闭) 的条件, True: 可以整单关闭
                whole_close_status = self.full_close_purchase(data_list, sku_result)

                for input_data in data_list:
                    print('skubarcode: {}'.format(input_data.get('skuBarcode')))
                    supplier_code = input_data.get('supplierCode')
                    # 查询供应商名称
                    supplier_name = Supplier().find_supplier_name_by_code(supplier_code)
                    if not supplier_name:
                        err_msg = "未查找到供应商: {}".format(supplier_code)
                        print(err_msg)
                        error_msg_str += ';{}'.format(err_msg)
                        print(error_msg_str)
                        sku_barcode_list.add(input_data['skuBarcode'])
                        data = {
                            'formId': self._data.get('formId'),
                            'bill_code': bill_code,
                            'skuBarcodeFailed': list(sku_barcode_list),
                            'skuBarcodeSuccessed': list(sku_barcode_success_list),
                        }
                        default_storage_redis.set(self.ClOSE_FAIL_TIMES_KEY, fail_times + 1)
                        return self.send_call_back_msg(error_msg_str, data_id=self._data_id, return_data=data)
                    input_data['supplierName'] = supplier_name
                    sku_operate_data = {}
                    for sku_data in sku_result:
                        if input_data['skuBarcode'] == sku_data['spec_code']:
                            sku_operate_data = sku_data
                    if not sku_operate_data:
                        err_msg = '没有找到对应商品编码sku:{} 的采购跟单'.format(input_data['skuBarcode'])
                        print(err_msg)
                        error_msg_str += ';{}'.format(err_msg)
                        print(error_msg_str)
                        sku_barcode_list.add(input_data['skuBarcode'])
                        continue

                    # 比较采购单的sku级别的数据和传入的关闭采购跟单数据
                    print('比较采购单的sku级别的数据和传入的关闭采购跟单:sku:{}的数据'.format(input_data['skuBarcode']))
                    status, msg = self.compare_close_purchase(input_data, sku_operate_data)
                    if status == 1:
                        err_msg = '抓取的数据字段:{}对不上;'.format(','.join(msg))
                        print(err_msg)
                        error_msg_str += '{}'.format(err_msg)
                        print(error_msg_str)
                        sku_barcode_list.add(input_data['skuBarcode'])
                        compared_pur_sku_status = True
                        continue

                    # 如果采购单在外部已经被关闭，跳过跟单的关闭
                    if purchase_bill_status:
                        print('采购单在外部已经被关闭,跳过跟单:{}的关闭'.format(input_data['skuBarcode']))
                        sku_barcode_list.remove(input_data['skuBarcode'])
                        sku_barcode_success_list.add(input_data['skuBarcode'])
                        continue

                    # 跳过已关闭的采购跟单
                    if int(sku_operate_data.get('status', 0)) in sku_invalid_close_list:
                        print('商品sku:{}对应的采购跟单已关闭或者全部到货,跳过'.format(input_data['skuBarcode']))
                        sku_barcode_list.remove(input_data['skuBarcode'])
                        sku_barcode_success_list.add(input_data['skuBarcode'])
                        continue

                    # 正式关闭采购跟单前，判断是整单关闭还是逐条关闭
                    if whole_close_status:
                        sku_barcode_list.remove(input_data['skuBarcode'])
                        sku_barcode_success_list.add(input_data['skuBarcode'])
                        continue

                    # 关闭对应的sku单
                    # 数据通过，删除数据
                    result_copy = deepcopy(result)
                    result_details_copy = deepcopy(result)
                    result_two_details = deepcopy(sku_operate_data)
                    sku_result_details_copy = deepcopy(sku_result)

                    result_two_whole_details = []
                    sku_result_whole_copy = deepcopy(sku_result)
                    for _r in sku_result_whole_copy:
                        if _r['spec_code'] == sku_operate_data['spec_code']:
                            continue
                        _r['$dataType'] = "v:purchase.bill$pchs_detail"
                        _r['$entityId'] = "0"
                        result_two_whole_details.append(_r)

                    result_two_details['$dataType'] = "v:purchase.bill$pchs_detail"
                    result_two_details['$state'] = 2
                    result_two_details['$entityId'] = "0"
                    result_two_details['$oldData'] = sku_operate_data
                    expecte_date = result_two_details['expecte_date']
                    result_two_details['expecte_date'] = expecte_date + 'T00:00:00Z' if isinstance(
                        expecte_date, str) and expecte_date else expecte_date
                    print('result_two_details: {}'.format(result_two_details['expecte_date']))
                    result_two_details['status'] = 3
                    result_copy['$dataType'] = "v:purchase.bill$purchaseBill"
                    result_copy['$state'] = 2
                    result_copy['$entityId'] = "0"
                    result_copy['bill_date'] = result_copy['bill_date'] + 'T00:00:00Z'
                    print('result_copy:{}'.format(result_copy['bill_date']))
                    result_copy['details'] = {
                        "$isWrapper": True,
                        "$dataType": "v:purchase.bill$[pchs_detail]",
                        "data": [result_two_details] + result_two_whole_details
                    }
                    result_details_copy['details'] = sku_result_details_copy
                    result_copy['$oldData'] = result_details_copy

                    sku_re_copy = deepcopy(sku_operate_data)
                    sku_re_copy['$dataType'] = "v:purchase.bill$pchs_detail"
                    sku_re_copy['$state'] = 2
                    sku_re_copy['$entityId'] = "0"
                    sku_re_date = sku_re_copy['expecte_date']
                    sku_re_copy['expecte_date'] = sku_re_date + 'T00:00:00Z' if isinstance(
                        sku_re_date, str) and sku_re_date else sku_re_date
                    print('sku_re_copy: {}'.format(sku_re_copy['expecte_date']))
                    sku_re_copy['status'] = 3
                    sku_re_copy['$oldData'] = sku_operate_data

                    # 开始关闭
                    close_msg = self.close_purchase_bill(bill_code, level=2, bill_data=result_copy,
                                                         close_remark=self.close_remark, bill_sku_data=sku_re_copy)
                    if 'error' in close_msg:
                        err_msg = '关闭商品编码: {} 对应的采购跟单失败，原因: {}'.format(input_data['skuBarcode'], close_msg)
                        error_msg_str += ';{}'.format(err_msg)
                        print(error_msg_str)
                    else:
                        print('关闭成功, skuBarcode:{}'.format(input_data['skuBarcode']))
                        sku_barcode_list.remove(input_data['skuBarcode'])
                        sku_barcode_success_list.add(input_data['skuBarcode'])

                # 判断是否要整单关闭
                if not purchase_bill_status and not compared_pur_sku_status and whole_close_status:
                    print("可以整单关闭采购单:{}".format(bill_code))
                    return_skubarcode = set()
                    for _d in data_list:
                        return_skubarcode.add(_d['skuBarcode'])
                    close_msg = self.close_purchase_bill(bill_code=bill_code, close_remark=self.close_remark)
                    if close_msg:
                        err_msg = '整单关闭采购单:{}失败,原因: {};'.format(bill_code, close_msg)
                        error_msg_str += err_msg
                        print(error_msg_str)
                        sku_barcode_list = return_skubarcode
                        sku_barcode_success_list.clear()
                    else:
                        print('整单关闭采购单:{}成功'.format(bill_code))
                        sku_barcode_list.clear()
                        sku_barcode_success_list = return_skubarcode

                data = {
                    'formId': self._data.get('formId'),
                    'bill_code': bill_code,
                    'skuBarcodeFailed': list(sku_barcode_list),
                    'skuBarcodeSuccessed': list(sku_barcode_success_list),
                }
                print('error_msg_str: {}'.format(error_msg_str))
                if error_msg_str:
                    self.send_call_back_msg(error_msg_str, data_id=self._data_id, return_data=data)
                    default_storage_redis.set(self.ClOSE_FAIL_TIMES_KEY, fail_times + 1)
                else:
                    # 发送成功关闭的消息
                    send_success_msg(bill_uid)
            else:
                # 没有数据，报警
                err_msg = '没有获取到被关闭的采购单: {} 的信息'.format(bill_code)
                print(err_msg)
                error_msg_str += ';{}'.format(err_msg)
                print(error_msg_str)
                data = {
                    'formId': self._data.get('formId'),
                    'bill_code': bill_code,
                    'skuBarcodeFailed': list(sku_barcode_list),
                    'skuBarcodeSuccessed': list(sku_barcode_success_list),
                }
                default_storage_redis.set(self.ClOSE_FAIL_TIMES_KEY, fail_times + 1)
                self.send_call_back_msg(error_msg_str, data_id=self._data_id, return_data=data)
        except Exception as e:
            print('----')
            print(traceback.format_exc())
            print('------')
            err_msg = '关闭采购订单时发生未知异常: {}; erpPurchaseNo:{}'.format(e, self._data.get('erpPurchaseNo'))
            print(err_msg)
            error_msg_str += ';{}'.format(err_msg)
            print(error_msg_str)
            data = {
                'formId': self._data.get('formId'),
                'bill_code': bill_code,
                'skuBarcodeFailed': list(sku_barcode_list),
                'skuBarcodeSuccessed': list(sku_barcode_success_list),
            }
            self.send_call_back_msg(error_msg_str, data_id=self._data_id, return_data=data)
            default_storage_redis.set(self.ClOSE_FAIL_TIMES_KEY, fail_times + 1)
            raise e

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
            if level == 1:
                result = PurchaseOrderClose() \
                    .set_param('bill_code', bill_code) \
                    .set_param('close_remark', close_remark) \
                    .get_result()
                result = json.loads(result)
                code = result.get('code')
                if code != 0:
                    if retry > 0:
                        return self.close_purchase_bill(bill_code, level, bill_data, bill_sku_data, close_remark,
                                                        retry - 1)
                    else:
                        # 发送关闭采购单失败的钉钉通知
                        title = '关闭采购单失败报警'
                        text = '关闭采购单失败了: {} 次, 需要手动去万里牛关闭异常订单: {}'.format(retry, bill_code)
                        DingTalk(ROBOT_TOKEN, title, text).enqueue()
                return result.get('message')
            else:
                result = CloseAudit(bill_data, bill_sku_data, remark=close_remark) \
                    .use_cookie_pool() \
                    .get_result(retry_limit=3, retry_interval=30)
            return result
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

    def compare_close_purchase(self, input_dict, crawl_sku_dict):
        """
        比较两个dict数据是否一样
        :param input_dict:
        :param crawl_sku_dict:
        :return:
        """
        lack_data = list()
        if input_dict['skuBarcode'] != crawl_sku_dict.get('spec_code'):
            lack_data.append('skuBarcode')
        if input_dict['purchaseCount'] != int(crawl_sku_dict.get('pchs_size')):
            lack_data.append('purchaseCount')
        if input_dict['arriveCount'] != int(crawl_sku_dict.get('pchs_receive')):
            lack_data.append('arriveCount')
        if lack_data:
            return 1, lack_data
        else:
            return 0, ''

    def full_close_purchase(self, data_list: list, sku_result: list):
        """
        判断是否能够整单关闭
        :param data_list: 传入的采购跟单信息
        :param sku_result: 查询到采购单对应的所有商品信息
        :return:
        """
        if len(data_list) >= len(sku_result):
            # 传入数量大于或等于查询到的采购单对应商品数量，肯定就可以整单关闭
            print('传入的采购跟单数量:{},查询到采购单对应的所有商品数量:{},可以整单关闭.'.format(len(data_list), len(sku_result)))
            return True
        whole_close = True
        # 选出相同的跟单
        same_items = set()
        for data in data_list:
            barcode = data.get('skuBarcode')
            for sku in sku_result:
                sku_spec_code = sku['spec_code']
                if barcode == sku_spec_code:
                    same_items.add(barcode)
        # 判断跟传入的跟单不同的商品是否都不能关闭,如果可以关闭，则代表不能整单关闭
        same_items_list = list(same_items)
        for _sku in sku_result:
            if _sku['spec_code'] in same_items_list:
                continue
            sku_status = int(_sku['status'])
            if sku_status != self.FULL_ARRIVED and sku_status != self.CLOSED:
                whole_close = False
        return whole_close

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
                err_msg, merge_str('CGGD', self._data.get('formId'), dividing=''), return_data.get('bill_code'))
            DingTalk(HUPUN_SYNC_ABNORMAL_ROBOT, title, ding_msg).enqueue()
            # 同时发送邮件通知
            if self._data.get('email'):
                EmailSender() \
                    .set_receiver(self._data.get('email')) \
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

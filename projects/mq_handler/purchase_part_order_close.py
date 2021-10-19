import traceback
from copy import deepcopy
from alarm.helper import Helper
from alarm.page.ding_talk import DingTalk
from cookie.config import ROBOT_TOKEN
from hupun.config import HUPUN_SEARCH_DAYS
from hupun_slow_crawl.model.es.supplier import Supplier
from hupun.page.purchase_order_goods_result import PurOrderGoodsResult
from hupun.page.purchase_order_query_result import POrderQueResult
from hupun_operator.page.purchase.close_audit import CloseAudit
from pyspider.helper.date import Date


class PurPartOrderClose:
    """
    !!! 已废弃，并不需要这个功能
    采购单跟单部分关闭, 同步操作(采购单更换供应商时的操作)
    """
    ClOSE_FAIL_TIMES_KEY = 'hupun_purchase_close_fails'  # redis中关闭订单失败次数的key
    # 采购订单不能关闭的状态值
    PUR_PARTIAL = 2  # 部分到货
    PUR_COMPLETE = 3  # 已完成
    PUR_CLOSED = 4  # 已关闭
    # 采购跟单的状态值
    NOT_ARRIVED = 0  # 未到货
    PARTIAL_ARRIVED = 1  # 部分到货
    FULL_ARRIVED = 2  # 全部到货, 不能操作关闭
    CLOSED = 3  # 已关闭, 不能操作关闭

    def __init__(self, bill_code, data_list, close_remark):
        self.bill_code = bill_code
        self.data_list = deepcopy(data_list)
        self.close_remark = close_remark

    def execute(self):
        print('开始关闭更换供应商的采购跟单')
        error_msg_str = ''
        sku_invalid_close_list = [self.FULL_ARRIVED, self.CLOSED]

        try:
            data_length = len(self.data_list)

            print('同步获取采购单: {}的数据'.format(self.bill_code))
            pur_order_query_obj = POrderQueResult(self.bill_code) \
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
                    err_msg = '采购单:{} 没有抓取到sku级别的采购跟单'.format(self.bill_code)
                    print(err_msg)
                    error_msg_str += ';{}'.format(err_msg)
                    print(error_msg_str)
                    return error_msg_str

                # 有数据，获取采购单的sku级别的数据
                print('有数据，获取采购单的sku级别的数据')
                if len(sku_result) < data_length:
                    err_msg = '关闭采购单: {} 失败, 因为传入到采购跟单数量是: {} ,大于爬虫抓取的数量: {}'.format(
                        self.bill_code, data_length, len(sku_result))
                    print(err_msg)
                    error_msg_str += ';{}'.format(err_msg)
                    print(error_msg_str)
                    return error_msg_str

                # 已完成，已关闭和部分到货的采购单 不能更改供应商
                if int(result.get('status', 0)) == self.PUR_CLOSED or int(result.get('status', 0)) == self.PUR_COMPLETE \
                        or int(result.get('status', 0)) == self.PUR_PARTIAL:
                    error_msg_str = '采购单:{}不能更改供应商, 已完成，已关闭和部分到货的采购单 不能更改供应商'.format(self.bill_code)
                    print('error_msg_str', error_msg_str)
                    return error_msg_str

                # 判断需要关闭的采购单是否满足 (整单关闭) 的条件, True: 可以整单关闭
                whole_close_status = self.full_close_purchase(self.data_list, sku_result)
                if whole_close_status:
                    error_msg_str = '采购单: {}可以整单关闭，不符合更改供应商的条件'.format(self.bill_code)
                    return error_msg_str

                for input_data in self.data_list:
                    print('sku barcode: {}'.format(input_data.get('skuBarcode')))
                    supplier_code = input_data.get('supplierCode')
                    # 查询供应商名称
                    supplier_name = Supplier().find_supplier_name_by_code(supplier_code)
                    if not supplier_name:
                        err_msg = "未查找到供应商: {}".format(supplier_code)
                        print(err_msg)
                        error_msg_str += ';{}'.format(err_msg)
                        print(error_msg_str)
                        return error_msg_str
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
                        continue

                    # 比较采购单的sku级别的数据和传入的关闭采购跟单数据
                    print('比较采购单的sku级别的数据和传入的关闭采购跟单:sku:{}的数据'.format(input_data['skuBarcode']))
                    status, msg = self.compare_close_purchase(input_data, sku_operate_data)
                    if status == 1:
                        err_msg = '抓取的数据字段:{}对不上;'.format(','.join(msg))
                        print(err_msg)
                        error_msg_str += '{}'.format(err_msg)
                        print(error_msg_str)
                        continue

                    # 跳过已关闭的采购跟单
                    if int(sku_operate_data.get('status', 0)) in sku_invalid_close_list:
                        print('商品sku:{}对应的采购跟单已关闭或者全部到货,跳过'.format(input_data['skuBarcode']))
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
                    close_msg = self.close_purchase_bill(self.bill_code, bill_data=result_copy,
                                                         close_remark=self.close_remark, bill_sku_data=sku_re_copy)
                    if 'error' in close_msg:
                        err_msg = '关闭商品编码: {} 对应的采购跟单失败，原因: {}'.format(input_data['skuBarcode'], close_msg)
                        error_msg_str += ';{}'.format(err_msg)
                        print(error_msg_str)
                    else:
                        print('关闭成功, skuBarcode:{}'.format(input_data['skuBarcode']))

                print('error_msg_str: {}'.format(error_msg_str))
            else:
                # 没有数据
                err_msg = '没有获取到被关闭的采购单: {} 的信息'.format(self.bill_code)
                print(err_msg)
                error_msg_str += ';{}'.format(err_msg)
                print(error_msg_str)
        except Exception as e:
            print('----')
            print(traceback.format_exc())
            print('------')
            err_msg = '关闭采购订单时发生未知异常: {}; erpPurchaseNo:{}'.format(e, self.bill_code)
            print(err_msg)
            error_msg_str += ';{}'.format(err_msg)
            print(error_msg_str)
        return error_msg_str

    def close_purchase_bill(self, bill_code='', bill_data='', bill_sku_data='', close_remark='', retry=3):
        """
        根据采购单据编码关闭采购订单;
        这个关闭的是第一层的采购订单（第一层指的是直接查询万里牛返回的面板信息）
        :param bill_code:
        :param bill_data:
        :param bill_sku_data:
        :param close_remark: 关闭备注
        :param retry: 重试次数
        :return:
        """
        try:
            result = CloseAudit(bill_data, bill_sku_data, remark=close_remark) \
                .use_cookie_pool() \
                .get_result(retry_limit=3, retry_interval=30)
            return result
        except Exception as e:
            print('--------error traceback--------')
            print(traceback.format_exc())
            print('close_purchase_bill close bill error: {}'.format(e))
            if retry > 0:
                return self.close_purchase_bill(bill_code, bill_data, bill_sku_data, close_remark, retry - 1)
            else:
                # 发送关闭采购单失败的钉钉通知
                title = '关闭采购单失败报警'
                text = '关闭采购单失败了: {} 次, 需要手动去万里牛关闭异常订单: {}'.format(retry, bill_code)
                DingTalk(ROBOT_TOKEN, title, text).enqueue()
                return 'error关闭采购单失败，重试次数: {}'.format(retry)

    @staticmethod
    def compare_close_purchase(input_dict, crawl_sku_dict):
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

# from mq_handler.base import Base
import json
import traceback
from copy import deepcopy

import time

from alarm.config import HUPUN_SYNC_ABNORMAL_ROBOT
from alarm.helper import Helper
from alarm.page.ding_talk import DingTalk
from hupun.config import HUPUN_SEARCH_DAYS
from hupun_slow_crawl.model.es.store_house import StoreHouse
from hupun_slow_crawl.model.es.supplier import Supplier
from hupun.page.sync_module.choose_purchase_bill import ChoosePurBill
from hupun.page.sync_module.choose_purchase_bill_sku import ChoosePurBillSku
from hupun.page.sync_module.confirm_purchase_stock import ConfirmPurBillStock
from hupun.page.sync_module.find_purchase_stock import FindPurStock
from hupun.page.sync_module.get_purchase_stock_token import PurchaseStockToken
from hupun.page.sync_module.submit_purchase_stock import SubmitPurBillStock
from hupun_api.page.purchase_stockin_order.stockin_order_add import StockinOrderAdd
from mq_handler.base import Base
from pyspider.helper.date import Date
from pyspider.helper.email import EmailSender


class PurchaseStockAdd(Base):
    """
    采购入库单的入库操作
    """

    def execute(self):
        print('采购入库单的入库操作')
        self.print_basic_info()

        # 写入数据
        try:
            self.api_operate_entry()
        except Exception as e:
            print('----------------traceback error----------------')
            print(traceback.format_exc())
            err = '采购单入库过程出现未知异常: {}'.format(e)
            print(err)
            self.send_call_back_msg(err_msg=err, data_id=self._data_id, status=1, erp_warehouse_no='',
                                    input_data=self._data)

    def api_operate_entry(self):
        """
        使用API接口的形式操作采购入库
        :return:
        """
        recv_data = deepcopy(self._data)
        # 返回的erp入库单号
        erp_warehouse_no = ''
        stockin_order_remark = 'spider-operation'
        bill_code = recv_data.get('erpPurchaseBill')
        storage_code = recv_data.get('storeHouseCode')
        supplier_code = recv_data.get('supplierCode')
        goods_list = recv_data.get('goodsList')
        storage_uid, storage_name = StoreHouse().get_uid_and_name_by_code(storage_code)
        supplier_uid = Supplier().find_supplier_uid_by_code(supplier_code)
        supplier_name = Supplier().find_supplier_name_by_code(supplier_code)

        # 判断接收到的采购入库单数据是否正确
        print('判断接收到的采购入库单数据是否正确')
        pur_bill_data_obj = ChoosePurBill(bill_code, storage_uid, storage_name, supplier_uid, supplier_name) \
            .set_start_time(Date.now().plus_days(-HUPUN_SEARCH_DAYS).format()) \
            .set_end_time(Date.now().format()) \
            .use_cookie_pool()
        pur_code, pur_bill_data = Helper().get_sync_result(pur_bill_data_obj)
        if pur_code == 1 or not pur_bill_data:
            error_msg = '在万里牛的采购入库单获取采购订单: {} 的数据失败,pur_code: {}'.format(bill_code, pur_code)
            if pur_bill_data:
                error_msg = '在万里牛的采购入库单获取采购订单: {} 的数据失败,pur_code: {}, error:{}'.format(bill_code, pur_code, pur_bill_data)
            print(error_msg)
            self.send_call_back_msg(err_msg=error_msg, data_id=self._data_id, status=1,
                                    erp_warehouse_no=erp_warehouse_no,
                                    input_data=recv_data)
            return
        bill_uid = pur_bill_data[0].get('bill_uid')
        print('bill_uid', bill_uid)

        pur_bill_sku_data_obj = ChoosePurBillSku(bill_uid).use_cookie_pool()
        pur_sku_code, pur_bill_sku_data = self.common_get_result(pur_bill_sku_data_obj)
        if pur_sku_code == 1 or not pur_bill_sku_data:
            error_msg = '在万里牛的采购入库单获取采购订单: {} 的商品详情数据数据失败'.format(bill_code)
            print(error_msg)
            self.send_call_back_msg(err_msg=error_msg, data_id=self._data_id, status=1,
                                    erp_warehouse_no=erp_warehouse_no,
                                    input_data=recv_data)
            return
        for _goods in goods_list:
            # 判断商品入库数量，小于1则报警
            if int(_goods.get('count')) < 1:
                error_msg = '接收到的入库数量为: {}, 小于1, 报警'.format(_goods.get('count'))
                print(error_msg)
                self.send_call_back_msg(err_msg=error_msg, data_id=self._data_id, status=1,
                                        erp_warehouse_no=erp_warehouse_no,
                                        input_data=recv_data)
                return
            for p_index, _data in enumerate(pur_bill_sku_data):
                spec_code = _data.get('spec_code')
                print('spec_code', spec_code)
                # 判断传入的数据是否存在查询到的数据里
                if _goods.get("skuBarcode") == spec_code:
                    # 如果传入的变动数量大于已有的数量，退出并报警
                    underway = _data.get('underway')
                    print('underway', underway)
                    if int(_goods.get('count')) > int(underway):
                        error_msg = '商品: {} 的变动数量: {} 大于万里牛已有的数量: {}'.format(
                            _goods.get('skuBarcode'), int(_goods.get('count')), int(underway))
                        print(error_msg)
                        self.send_call_back_msg(err_msg=error_msg, data_id=self._data_id, status=1,
                                                erp_warehouse_no=erp_warehouse_no, input_data=recv_data)
                        return
                    break
                else:
                    if p_index == len(pur_bill_sku_data) - 1:
                        error_msg = '商品: {}在万里牛的采购入库单里查不到'.format(_goods.get('skuBarcode'))
                        print(error_msg)
                        self.send_call_back_msg(err_msg=error_msg, data_id=self._data_id, status=1,
                                                erp_warehouse_no=erp_warehouse_no, input_data=recv_data)
                        return

        # 调用采购入库单的API
        print('调用采购入库单的API')
        details = []
        for _data in goods_list:
            inner_data = {
                'nums': int(_data.get('count')),
                'spec_code': _data.get('skuBarcode'),
                'pchs_bill_code': recv_data.get('erpPurchaseBill')
            }
            details.append(inner_data)
        bill_date = Date.now().millisecond()
        js_data = {
            'bill_date': bill_date,
            'details': details,
            'storage_code': recv_data.get('storeHouseCode'),
            'supplier_code': recv_data.get('supplierCode'),
            'pchs_bill_code': recv_data.get('erpPurchaseBill'),
            'remark': stockin_order_remark,
        }

        # 添加延迟重试
        retry_times = 3
        api_code = -1
        result = ""
        js_result = {}
        for i in range(retry_times):
            result = StockinOrderAdd().set_param('bill', js_data).get_result()
            js_result = json.loads(result)
            api_code = int(js_result.get('code'))
            api_err_msg = js_result.get('message', "")

            if api_code == 0:
                break
            elif api_err_msg and "应用调用超过频次" in api_err_msg:
                try:
                    sleep_time = int(api_err_msg.split("限制调用", 1)[1].split("秒", 1)[0].strip())
                    print("延迟:{}s重试万里牛API调用".format(sleep_time))
                    time.sleep(sleep_time)
                except Exception as e:
                    print("解析万里牛API操作报错结果失败", e)
            else:
                break

        if api_code == 0:
            print('成功入库采购单: {}, 返回结果: {}'.format(bill_code, result))
            erp_warehouse_no = js_result.get('data')
            self.send_call_back_msg(err_msg='', data_id=self._data_id, status=0, erp_warehouse_no=erp_warehouse_no,
                                    input_data=recv_data)
        else:
            error_msg = '入库失败,万里牛采购单号:{};返回结果:{};'.format(bill_code, js_result.get('data'))
            if js_result.get('message'):
                error_msg += ':'.join(['err_msg', js_result.get('message')])
            print(error_msg)
            self.send_call_back_msg(err_msg=error_msg, data_id=self._data_id, status=1,
                                    erp_warehouse_no=erp_warehouse_no, input_data=recv_data)

    def main(self, data):
        """
        爬虫的方式进行采购入库操作，现在被API代替，已弃用
        :param data:
        :return:
        """
        data_id = self._data_id
        recv_data = deepcopy(data)
        # 返回的erp入库单号
        erp_warehouse_no = ''

        # 查找 采购单 返回的数据
        bill_code = recv_data.get('erpPurchaseBill')
        storage_code = recv_data.get('storeHouseCode')
        supplier_code = recv_data.get('supplierCode')
        goods_list = recv_data.get('goodsList')
        storage_uid, storage_name = StoreHouse().get_uid_and_name_by_code(storage_code)
        storage_type = StoreHouse().get_storage_type_by_code(storage_code)
        supplier_uid = Supplier().find_supplier_uid_by_code(supplier_code)
        supplier_name = Supplier().find_supplier_name_by_code(supplier_code)

        pur_bill_data_obj = ChoosePurBill(bill_code, storage_uid, storage_name, supplier_uid, supplier_name) \
            .set_start_time(Date.now().plus_days(-90).format()) \
            .set_end_time(Date.now().format()) \
            .use_cookie_pool()
        pur_code, pur_bill_data = self.common_get_result(pur_bill_data_obj)
        if pur_code == 1 or not pur_bill_data:
            error_msg = '在万里牛获取采购单: {} 的数据失败'.format(bill_code)
            print(error_msg)
            self.send_call_back_msg(err_msg=error_msg, data_id=data_id, status=1, erp_warehouse_no=erp_warehouse_no,
                                    input_data=data)
            return
        bill_uid = pur_bill_data[0].get('bill_uid')
        print('bill_uid', bill_uid)

        # 本次同步入库的总数量
        all_instock_num = 0
        for _g in goods_list:
            all_instock_num += int(_g.get('count'))

        # 查找 采购单商品 返回的数据

        # 采购单下的商品构造数据
        submit_data = [
            {
                "$dataType": "v:purchase.stock$dtStockBillDetail"
            }
        ]
        pur_bill_sku_data_obj = ChoosePurBillSku(bill_uid).use_cookie_pool()
        pur_sku_code, pur_bill_sku_data = self.common_get_result(pur_bill_sku_data_obj)
        if pur_sku_code == 1 or not pur_bill_sku_data:
            error_msg = '在万里牛获取采购单: {} 的商品详情数据数据失败'.format(bill_code)
            print(error_msg)
            self.send_call_back_msg(err_msg=error_msg, data_id=data_id, status=1, erp_warehouse_no=erp_warehouse_no,
                                    input_data=data)
            return
        for _goods in goods_list:
            # 判断商品入库数量，小于1则报警
            if int(_goods.get('count')) < 1:
                error_msg = '接收到的入库数量为: {}, 小于1, 报警'.format(_goods.get('count'))
                print(error_msg)
                self.send_call_back_msg(err_msg=error_msg, data_id=data_id, status=1, erp_warehouse_no=erp_warehouse_no,
                                        input_data=data)
                return
            for p_index, _data in enumerate(pur_bill_sku_data):
                spec_code = _data.get('spec_code')
                print('spec_code', spec_code)
                # 判断传入的数据是否存在查询到的数据里
                if _goods.get("skuBarcode") == spec_code:
                    # 如果传入的变动数量大于已有的数量，退出并报警
                    underway = _data.get('underway')
                    print('underway', underway)
                    if int(_goods.get('count')) > int(underway):
                        error_msg = '商品: {} 的变动数量: {} 大于万里牛已有的数量: {}'.format(
                            _goods.get('skuBarcode'), int(_goods.get('count')), int(underway))
                        print(error_msg)
                        self.send_call_back_msg(err_msg=error_msg, data_id=data_id, status=1,
                                                erp_warehouse_no=erp_warehouse_no, input_data=data)
                        return
                    data = self.get_submit_data(_data, _goods)
                    submit_data.append(data)
                    break
                else:
                    if p_index == len(pur_bill_sku_data) - 1:
                        error_msg = '商品: {}在万里牛的采购入库单里查不到'.format(_goods.get('skuBarcode'))
                        print(error_msg)
                        self.send_call_back_msg(err_msg=error_msg, data_id=data_id, status=1,
                                                erp_warehouse_no=erp_warehouse_no, input_data=data)
                        return

        # 提交变动申请
        submit_compare_data_obj = SubmitPurBillStock(submit_data).use_cookie_pool()
        sub_code, submit_compare_data = self.common_get_result(submit_compare_data_obj)
        if sub_code == 1:
            error_msg = '提交变动申请失败: {}'.format(submit_compare_data)
            print(error_msg)
            self.send_call_back_msg(err_msg=error_msg, data_id=data_id, status=1,
                                    erp_warehouse_no=erp_warehouse_no, input_data=data)
            return

        # 对比确认提交申请前的数据
        if sub_code == 0 and submit_compare_data:
            error = self.compare_data(recv_data, submit_compare_data)
            if error:
                error_msg = '对比有问题的数据:{}'.format(':'.join(error))
                print(error_msg)
                self.send_call_back_msg(err_msg=error_msg, data_id=data_id, status=1,
                                        erp_warehouse_no=erp_warehouse_no, input_data=data)
                return

        # 确认提交申请
        print('确认提交申请')
        confirm_data = self.get_confirm_data(pur_bill_data[0], submit_data, storage_type)
        result_msg_obj = ConfirmPurBillStock(confirm_data).use_cookie_pool()
        re_code, result_msg = self.common_get_result(result_msg_obj)
        if re_code == 1 or not result_msg:
            if re_code == 0:
                error_msg = '确认提交申请失败: 确认提交申请后的返回数据为空'
            else:
                error_msg = '确认提交申请失败: {}'.format(result_msg)
            print(error_msg)
            self.send_call_back_msg(err_msg=error_msg, data_id=data_id, status=1,
                                    erp_warehouse_no=erp_warehouse_no, input_data=data)
            return
        # 入库成功时的时间
        bill_create_date = result_msg.get('0').get('bill_date')
        bill_create_more_date = Date(bill_create_date).plus_seconds(5)
        print('bill_create_date', bill_create_date)

        # 获取本次生成的单据编号并发送成功生成的消息
        find_pur_obj = FindPurStock(storage_uid, storage_name, supplier_uid, supplier_name).use_cookie_pool()
        f_code, find_pur = self.common_get_result(find_pur_obj)
        if f_code == 1 or not find_pur:
            error_msg = '已经成功同步了采购入库单，但在获取新生成的单据编号时失败了，请手动处理本次采购单: {}, 成功同步的时间为: {}'.format(bill_code, bill_create_date)
            print(error_msg)
            self.send_call_back_msg(err_msg=error_msg, data_id=data_id, status=1,
                                    erp_warehouse_no=erp_warehouse_no, input_data=data)
            return

        # 获取本次生成的单据编号
        for _pur in find_pur:
            pur_time = Date(_pur.get('modified_time'))
            if storage_uid == _pur.get('storage_uid') and storage_name == _pur.get('storage_name') and \
                supplier_uid == _pur.get('supplier_uid') and supplier_name == _pur.get('supplier_name') \
                and bill_uid == _pur.get('pchs_bill_uid') and all_instock_num == int(_pur.get('pchsSum')) \
                and pur_time < bill_create_more_date \
                and (Date(bill_create_date) < pur_time or Date(bill_create_date) == pur_time):
                erp_warehouse_no = _pur.get('stock_code')
                break
        print('erp_warehouse_no', erp_warehouse_no)
        if not erp_warehouse_no:
            error_msg = '已经成功同步了采购入库单，但在获取新生成的单据编号时失败了，请手动处理本次采购单: {}, 成功同步的时间为: {}'.format(bill_code, bill_create_date)
            print(error_msg)
            self.send_call_back_msg(err_msg=error_msg, data_id=data_id, status=1,
                                    erp_warehouse_no=erp_warehouse_no, input_data=data)
        else:
            self.send_call_back_msg(err_msg='', data_id=data_id, status=0, erp_warehouse_no=erp_warehouse_no,
                                    input_data=data)

    def get_submit_data(self, data: dict, input_data: dict):
        """
        处理成提交采购入库申请的格式
        :param data: 爬虫从万里牛抓取到的数据
        :param input_data: 从中间件传入的数据
        :return:
        """
        return_dict = {}
        return_dict['goodsUid'] = data.get('goods_uid')
        return_dict['goodsName'] = data.get('goods_name')
        return_dict['specUid'] = data.get('spec_uid')
        return_dict['pic1'] = data.get('pic1')
        return_dict['specCode'] = data.get('spec_code')
        return_dict['specName'] = data.get('spec_name')
        return_dict['unit_size'] = data.get('unit_size')
        return_dict['pchs_unit'] = data.get('pchs_unit')
        return_dict['unit'] = data.get('unit')
        return_dict['shouldNums'] = data.get('underway', 1)
        return_dict['nums'] = input_data.get('count', 0)
        return_dict['discount_rate'] = data.get('discount_rate')
        return_dict['price'] = data.get('price')
        return_dict['pivtLast'] = data.get('pchs_base_price')
        return_dict['primePrice'] = data.get('pchs_price')
        return_dict['base_price'] = data.get('base_price')
        return_dict['tax_rate'] = data.get('tax_rate')
        return_dict['pchs_bill_uid'] = data.get('bill_uid')
        return_dict['pchs_bill_code'] = data.get('bill_code')
        return_dict['appointBillType'] = data.get('bill_type')
        return_dict['pchs_detail_uid'] = data.get('detail_uid')
        return_dict['pchs_detail_index'] = data.get('detail_index')
        return_dict['remark'] = data.get('remark')
        return_dict['openSN'] = data.get('openSN')
        return_dict['expiration'] = data.get('expiration')
        return_dict['total_money'] = int(return_dict['nums']) * float(return_dict['price'])
        return_dict['pay_type'] = data.get('pay_type')
        return_dict['pchs_advance_balance'] = data.get('pchs_advance_balance')
        return_dict['stock_advance_balance'] = data.get('stock_advance_balance')
        return_dict['settle_advance_balance'] = data.get('settle_advance_balance')
        return_dict['tax'] = data.get('tax')
        return_dict['net_price'] = data.get('net_price')
        return_dict['sn'] = None if data.get('openSN') == 0 else data.get('openSN')
        return_dict['$dataType'] = 'v:purchase.stock$dtStockBillDetail'
        return return_dict

    def get_confirm_data(self, bill_data: dict, submit_data: list, storage_type):
        """
        构造提交申请前的数据结构
        :param bill_data: 爬虫获取到的采购单数据
        :param submit_data: 提交申请时构造的数据
        :param storage_type: 仓库的类型
        :return:
        """
        # 第一层数据
        first_dict = {}
        bill_date = Date.now().format_es_old_utc()
        first_dict['bill_type'] = 6
        first_dict['status'] = bill_data.get('status')
        first_dict['bill_date'] = bill_date
        first_dict['storage_uid'] = bill_data.get('storage_uid')
        first_dict['storage_name'] = bill_data.get('storage_name')
        first_dict['storageType'] = storage_type
        first_dict['sumprice'] = 0
        first_dict['payment'] = 0
        first_dict['advance_balance'] = 0 if bill_data.get('pchs_advance_balance') is None else bill_data.get(
            'pchs_advance_balance')
        first_dict['debt'] = 0  # 本次提交申请的商品总额
        first_dict['settlement'] = 0 if bill_data.get('settle_advance_balance') is None else bill_data.get(
            'settle_advance_balance')
        first_dict['haveDebt'] = False
        first_dict['carriage'] = 0
        first_dict['price'] = 0 if bill_data.get('price') is None else bill_data.get('price')
        first_dict['rebatePrice'] = 0
        first_dict['rebate'] = 0
        first_dict['rowSelect'] = bill_data.get('rowSelect')
        first_dict['currencyCode'] = bill_data.get('currencyCode')
        first_dict['currencyName'] = '人民币'
        first_dict['currencySymbol'] = bill_data.get('currencySymbol')
        first_dict['account_uid'] = '60803EF0B4883CF6A9238344C5590B2C'
        first_dict['account_name'] = '系统账户'
        first_dict['pchs_bill_uid'] = bill_data.get('bill_uid')
        first_dict['pchs_bill_code'] = None  # bill_data.get('bill_code')
        first_dict['supplier_uid'] = bill_data.get('supplier_uid')
        first_dict['supplier_name'] = bill_data.get('supplier_name')
        first_dict['saleman'] = bill_data.get('saleman')
        first_dict['salemanUid'] = bill_data.get('salemanUid')
        first_dict['$dataType'] = 'v:purchase.stock$dtStcockBill'
        first_dict['$state'] = 1
        first_dict['$entityId'] = "0"
        first_dict['detail'] = {
            '$isWrapper': True,
            '$dataType': 'v:purchase.stock$[dtStockBillDetail]',
        }

        # 第二层数据
        sku_list = []
        submit_sum_price = 0
        for _submit in submit_data:
            if len(_submit) == 1:
                _submit['$state'] = 1
                _submit['$entityId'] = "0"
            else:
                submit_sum_price += int(_submit['nums']) * float(_submit['price'])
                _submit['$state'] = 2
                _submit['$entityId'] = "0"
            sku_list.append(_submit)
        first_dict['detail']['data'] = sku_list
        first_dict['debt'] = submit_sum_price

        # token
        token_obj = PurchaseStockToken().use_cookie_pool()
        t_code, token = self.common_get_result(token_obj)
        if t_code == 1:
            assert False, '确认提交采购入库操作时的token获取失败'

        # 拼接整个确认提交申请的数据
        final_data = {
            "action": "resolve-data",
            "parameter": {
                "token": token
            },
            "context": {},
            "dataResolver": "stockBillInterceptor#saveStockBill",
            "dataItems": [
                {
                    "alias": "dsStockBill",
                    "data": {
                        "$isWrapper": True,
                        "$dataType": "v:purchase.stock$[dtStcockBill]",
                        'data': first_dict
                    },
                    "refreshMode": "value",
                    "autoResetEntityState": True
                }
            ]
        }
        return final_data

    def compare_data(self, input_data, pre_submit_data):
        """
        对比提交申请前的数据
        :param input_data: 中间件接收到的数据
        :param pre_submit_data: 提交申请时返回的数据
        :return:
        """
        error_msg = []
        goods_list = input_data.get('goodsList')
        for _input in goods_list:
            for p_index, _submit in enumerate(pre_submit_data):
                if _input['skuBarcode'] == _submit['specCode']:
                    break
                elif _input['skuBarcode'] != _submit['specCode'] and p_index == len(pre_submit_data) - 1:
                    error_msg.append('skuBarcode:{}'.format(_input['skuBarcode']))
        return error_msg

    def common_get_result(self, obj, retry=3, delay_time=15):
        """
        通用的获取同步爬虫请求的方法
        :param obj: 同步爬虫的实例
        :param retry: 重试次数
        :param delay_time: 延时时间
        :return:
        """
        try:
            print('获取爬虫: {} 的同步数据'.format(obj.__class__.__name__))
            result = obj.get_result()
            return 0, result
        except Exception as e:
            print('爬虫同步请求的error: {}'.format(e))
            if retry > 0:
                time.sleep(int(delay_time))
                return self.common_get_result(obj, retry - 1)
            else:
                err = '爬虫: {} 同步获取数据重试次数剩余: {} 次,退出'.format(obj.__class__.__name__, retry)
                return 1, err

    def send_call_back_msg(self, err_msg='', data_id='', status=1, erp_warehouse_no='', input_data=''):
        """
        发送返回的消息数据
        :param err_msg: 错误信息详情
        :param data_id: 消息中间件的 data_id
        :param status: 消息状态，1: 失败; 0: 成功
        :param erp_warehouse_no: 成功
        :param input_data: 中间件传过来的同步操作数据
        :return:
        """
        return_msg = {
            "code": status,  # 0：成功 1：失败
            "errMsg": err_msg,  # 如果code为1，请将失败的具体原因返回
            "erpWarehouseNum": erp_warehouse_no
        }
        print('发送返回的消息数据: {}'.format(return_msg))

        if status != 0 and Helper.in_project_env():
            # 发送失败的消息
            title = '万里牛入库单同步操作失败'
            ding_msg = '万里牛入库单同步操作失败原因: {}, 天鸽采购单号: {}, 万里牛采购单号: {}, 入库单号: {}'.format(
                err_msg, input_data.get('tgPurchaseBill'), input_data.get('erpPurchaseBill'), self._data_id)
            DingTalk(HUPUN_SYNC_ABNORMAL_ROBOT, title, ding_msg).enqueue()
            # 同时发送邮件通知
            if self._data.get('email'):
                EmailSender() \
                    .set_receiver(self._data.get('email')) \
                    .set_mail_title(title) \
                    .set_mail_content(ding_msg) \
                    .send_email()

        from mq_handler import CONST_MESSAGE_TAG_PURCHARSE_STOCK_RESULT
        from mq_handler import CONST_ACTION_UPDATE
        from pyspider.libs.mq import MQ
        msg_tag = CONST_MESSAGE_TAG_PURCHARSE_STOCK_RESULT
        return_date = Date.now().format()
        MQ().publish_message(msg_tag, return_msg, data_id, return_date, CONST_ACTION_UPDATE)

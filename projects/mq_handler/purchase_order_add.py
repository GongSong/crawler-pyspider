import json
import time
import traceback
from copy import deepcopy

from alarm.config import HUPUN_SYNC_ABNORMAL_ROBOT
from alarm.helper import Helper
from alarm.page.ding_talk import DingTalk
from cookie.config import ROBOT_TOKEN
from hupun.model.es.purchase_order_add_msg import PurOrderAddMsg
from hupun_slow_crawl.model.es.store_house import StoreHouse
from hupun_slow_crawl.model.es.supplier import Supplier
from hupun.page.purchase_order import PurchaseOrder
from hupun.page.purchase_order_goods_result import PurOrderGoodsResult
from hupun.page.purchase_order_result import PurchaseOrderResult
from hupun_api.page.purchase_order_add import PurchaseOrderAdd as PurChaseOrAdd
from hupun_api.page.purchase_order_close import PurchaseOrderClose
from hupun_operator.page.purchase.close_audit import CloseAudit
from hupun_operator.page.purchase.submit_audit import SubmitAudit
from mq_handler.base import Base
from pyspider.core.model.storage import default_storage_redis
from pyspider.helper.date import Date
from pyspider.helper.email import EmailSender


class PurchaseOrderAdd(Base):
    """
    添加采购订单
    """
    # 采购订单的状态值
    NOT_ARRIVED = 1  # 未到货
    CLOSED = 4  # 已关闭
    PENDING = 5  # 待提交
    AUDITTING = 6  # 审核中
    ADD_FAIL_TIMES_KEY = 'hupun_purchase_add_fails'  # redis中增加订单失败次数的key

    # 同步采购单的操作类型
    SENDED_TYPE_MANUAL = 1  # 手动创建的采购单
    SENDED_TYPE_AUTO = 2  # 自动（补充）创建的采购单
    SENDED_TYPE_COPY = 3  # 更改供应商新建采购单（复制原有采购单）

    def execute(self):
        print('添加采购订单')
        self.print_basic_info()
        data = self._data
        close_remark = '爬虫自己在执行过程中的关闭,不包含天鸽发起的关闭'
        added_bill_code = ''

        # 从redis获取的之前连续失败的次数，如大于等于9则告警并将该值重新置零。
        fail_times = default_storage_redis.get(self.ADD_FAIL_TIMES_KEY)
        if not fail_times:
            print('错误，未获取到fail_times的值！')
            default_storage_redis.set(self.ADD_FAIL_TIMES_KEY, 0)
            fail_times = 0
        else:
            fail_times = int(fail_times)
        if fail_times >= 9:
            ding_msg = '已连续10次未正确同步erp的采购订单添加操作，请及时上线检查。'
            print(ding_msg)
            title = '同步采购订单的程序警告'
            DingTalk(ROBOT_TOKEN, title, ding_msg).enqueue()
            fail_times = 0
            default_storage_redis.set(self.ADD_FAIL_TIMES_KEY, 0)

        try:
            api_details = list()
            storage_code = data.get('list')[0].get('storageCode', '')
            supplier_code = data.get('list')[0].get('supplierCode', '')

            # 检查天鸽单号之前是否已成功同步
            tg_purchase_no = data.get('list')[0].get('purchaseNo', '')
            success_bill_code = self.sended_success_msg(tg_purchase_no, storage_code, data.get("isSecond", False))
            if success_bill_code and data.get('type') != self.SENDED_TYPE_AUTO:
                err_msg = '该天鸽单号之前已同步成功，为重复单号，已忽略。'
                print(err_msg)
                return self.send_call_back_msg(data, status=0, data_id=self._data_id, erp_purch_no=success_bill_code)

            # 查找仓库
            storage_uid, storage_name = StoreHouse().get_uid_and_name_by_code(storage_code)
            print('storage_uid: {}, storage_name: {}'.format(storage_uid, storage_name))
            if not storage_uid:
                err_msg = "未查找到仓库: {}".format(storage_name)
                default_storage_redis.set(self.ADD_FAIL_TIMES_KEY, fail_times + 1)
                return self.send_call_back_msg(data, err_msg, data_id=self._data_id)
            # 查询供应商名称
            supplier_name = Supplier().find_supplier_name_by_code(supplier_code)
            print('supplier_name: {}'.format(supplier_name))
            if not supplier_name:
                err_msg = "未查找到供应商: {}".format(supplier_code)
                default_storage_redis.set(self.ADD_FAIL_TIMES_KEY, fail_times + 1)
                return self.send_call_back_msg(data, err_msg, data_id=self._data_id)
            for _data in data.get('list'):
                if int(_data.get('status', 0)) == 1 and data.get('type') == self.SENDED_TYPE_COPY:
                    # 采购单里商品的状态如果为关闭, 并且是需要复制的采购单, 则跳过这个商品的添加采购单
                    continue

                data_dict = dict()
                _data['supplierName'] = supplier_name
                _data['storageName'] = storage_name
                data_dict['price'] = float(_data['price'])
                data_dict['size'] = int(_data['purchaseCount'])
                data_dict['spec_code'] = _data['skuBarcode']
                data_dict['sum'] = float(_data['price']) * int(_data['purchaseCount'])
                api_details.append(data_dict)
            js_data = {
                'storage_code': storage_code,
                'supplier_code': supplier_code,
                'remark': data.get('list')[0].get('remark'),
                'details': api_details
            }
            add_api_result = PurChaseOrAdd().set_param('bill', js_data).get_result(retry_limit=3)
            add_api_result = json.loads(add_api_result)
            print('调用添加采购单API的结果: {}'.format(add_api_result))
            if add_api_result.get('code') != 0:
                # 发送错误消息
                err_msg = add_api_result.get('message')
                print(err_msg)
                # 删除同步失败的采购订单
                # if len(err_msg.split(';bill:')) > 1:
                #     cbill_code = err_msg.split(';bill:')[-1]
                #     close_msg = self.close_purchase_bill(cbill_code, close_remark=close_remark)
                #     err_msg += close_msg
                default_storage_redis.set(self.ADD_FAIL_TIMES_KEY, fail_times + 1)
                return self.send_call_back_msg(data, err_msg, data_id=self._data_id)

            bill_code = add_api_result.get('data')
            print('提交订单bill_code: {}'.format(bill_code))
            added_bill_code = bill_code

            # 在提交订单之前，需要下发一个强制更新hupun cookie的任务，用来保证获取采购订单号数据可以正确执行
            # 如果不这样做，执行到这一步之后，cookie会失效，导致下一步执行失败。这个原因目前还不清楚
            # 2019-07-18 更新：不需要强制更新cookie的操作了
            # time.sleep(10)
            # 提交订单，获取采购订单号对应的结构化数据
            first_data = self.fetch_bill_data(bill_code)
            time.sleep(2)
            if not first_data:
                err_msg = '未获取到采购订单: {}, 同步失败，中断并退出。'.format(bill_code)
                # 删除同步失败的采购订单
                close_msg = self.close_purchase_bill(bill_code, close_remark=close_remark)
                err_msg += ';关闭采购单的返回信息:{}'.format(close_msg)
                print(err_msg)
                default_storage_redis.set(self.ADD_FAIL_TIMES_KEY, fail_times + 1)
                return self.send_call_back_msg(data, err_msg, data_id=self._data_id)

            # 判断订单状态
            bill_status = int(first_data['status'])
            if bill_status == self.PENDING:
                # 等待中，提交审核
                result = SubmitAudit(first_data).use_cookie_pool().get_result(retry_limit=3)
                print('等待中, 提交审核, result: {}'.format(result))
                if result:
                    # 有事发生，处理事故
                    err_msg = 'err: {}'.format(result)
                    print('有事发生，处理事故, {}'.format(err_msg))
                    # 删除同步失败的采购订单
                    close_msg = self.close_purchase_bill(bill_code, close_remark=close_remark)
                    err_msg += ';关闭采购单的返回信息:{}'.format(close_msg)
                    default_storage_redis.set(self.ADD_FAIL_TIMES_KEY, fail_times + 1)
                    return self.send_call_back_msg(data, err_msg, data_id=self._data_id)
                else:
                    print('提交成功，继续流程')
            else:
                err_msg = '流程不正确，订单状态不为: {}, 退出'.format(self.PENDING)
                print(err_msg)
                # 删除同步失败的采购订单
                close_msg = self.close_purchase_bill(bill_code, close_remark=close_remark)
                err_msg += ';关闭采购单的返回信息:{}'.format(close_msg)
                default_storage_redis.set(self.ADD_FAIL_TIMES_KEY, fail_times + 1)
                return self.send_call_back_msg(data, err_msg, data_id=self._data_id)

            # 对比审核前的采购单数据，不一样的话则中断本次提交并返回失败的信息
            second_data = self.fetch_bill_data(bill_code)
            bill_status = int(second_data['status'])
            bill_uid = second_data['bill_uid']
            sku_data = self.fetch_purchase_sku(bill_uid)
            if not sku_data:
                # 删除同步失败的采购订单
                close_msg = self.close_purchase_bill(bill_code, close_remark=close_remark)
                err_msg = '在比较审核前的数据时未获取到爬虫抓取的sku_barcode'
                err_msg += ';关闭采购单的返回信息:{}'.format(close_msg)
                default_storage_redis.set(self.ADD_FAIL_TIMES_KEY, fail_times + 1)
                return self.send_call_back_msg(data, err_msg, data_id=self._data_id)

            if bill_status == self.AUDITTING:
                # 审核中，对比数据后，确认数据通过与否
                print('审核中，对比数据后，确认数据通过与否')
                status, msg = self.compare_add_purchase(data, second_data, sku_data)
                if status == 1:
                    err_msg = '抓取的数据缺少字段:{}'.format(','.join(list(msg)))
                    print(err_msg)
                    # 删除同步失败的采购订单
                    close_msg = self.close_purchase_bill(bill_code, close_remark=close_remark)
                    err_msg += ';关闭采购单的返回信息:{}'.format(close_msg)
                    default_storage_redis.set(self.ADD_FAIL_TIMES_KEY, fail_times + 1)
                    return self.send_call_back_msg(data, err_msg, data_id=self._data_id)

                # 通过了字段对比，审核通过
                result = SubmitAudit(second_data).use_cookie_pool().get_result(retry_limit=3)
                if result:
                    # 有事发生，处理事故
                    err_msg = '审核提交失败: {}'.format(result)
                    print(err_msg)
                    # 删除同步失败的采购订单
                    close_msg = self.close_purchase_bill(bill_code, close_remark=close_remark)
                    err_msg += ';关闭采购单的返回信息:{}'.format(close_msg)
                    default_storage_redis.set(self.ADD_FAIL_TIMES_KEY, fail_times + 1)
                    return self.send_call_back_msg(data, err_msg, data_id=self._data_id)
                else:
                    print('通过了审核，返回单据编号: {}'.format(bill_code))

                    # 保存发过来的原始数据
                    save_list = []
                    save_data = dict()
                    save_data['supplier_name'] = supplier_name
                    save_data['storage_name'] = storage_name
                    save_data['bill_code'] = bill_code
                    save_data['create_time'] = Date.now().format_es_old_utc()
                    save_data['check_status'] = False
                    save_data['goods'] = []
                    for _d in api_details:
                        save_data_good = dict()
                        save_data_good['sku_barcode'] = _d.get('spec_code')
                        save_data_good['purchase_count'] = _d.get('size')
                        save_data_good['price'] = _d.get('price')
                        save_data['goods'].append(save_data_good)
                    save_list.append(save_data)
                    PurOrderAddMsg().update(save_list, async=True)
                    print('已存入es：{}'.format(save_list))
                    # 同步成功后更新一遍采购单
                    PurchaseOrder(True) \
                        .set_start_time(Date.now().plus_days(-1).format()) \
                        .set_priority(PurchaseOrder.CONST_PRIORITY_FIRST) \
                        .use_cookie_pool() \
                        .enqueue()
                    # 成功后，将连续失败次数设置为0
                    default_storage_redis.set(self.ADD_FAIL_TIMES_KEY, 0)
                    return self.send_call_back_msg(data, status=0, data_id=self._data_id, erp_purch_no=bill_code)

            else:
                err_msg = '审核流程不正确，删除该采购订单并退出，该采购单目前的状态status: {}'.format(bill_status)
                print(err_msg)
                # 删除同步失败的采购订单
                close_msg = self.close_purchase_bill(bill_code, close_remark=close_remark)
                err_msg += ';关闭采购单的返回信息:{}'.format(close_msg)
                return self.send_call_back_msg(data, err_msg, data_id=self._data_id)
        except Exception as e:
            print('同步采购订单时发生未知异常: {}'.format(e))
            print('--------error traceback--------')
            print(traceback.format_exc())
            err_msg = '同步采购订单时发生未知异常'
            self.send_call_back_msg(data, err_msg, data_id=self._data_id)
            if added_bill_code:
                self.close_purchase_bill(added_bill_code, close_remark=close_remark)
            raise e

    def fetch_bill_data(self, bill_code, retry=4):
        """
        基于单据编号返回对应的代购订单数据
        :param bill_code:
        :param retry:
        :return:
        """
        try:
            print('bill_code: {}'.format(bill_code))
            result = PurchaseOrderResult(bill_code) \
                .set_start_time(Date.now().plus_days(-30).format()) \
                .set_end_time(Date.now().format()) \
                .use_cookie_pool() \
                .get_result()
            if result:
                return result
            else:
                return {}
        except Exception as e:
            print('--------error traceback--------')
            print(traceback.format_exc())
            print('获取采购订单sku详情的error: {}'.format(e))
            if retry > 0:
                retry -= 1
                time.sleep(25)
                return self.fetch_bill_data(bill_code, retry)
            else:
                return {}

    def fetch_purchase_sku(self, bill_uid, retry=4):
        """
        获取单条的采购单的sku数据
        :param bill_uid:
        :param retry:
        :return:
        """
        try:
            print('bill_uid: {}'.format(bill_uid))
            result = PurOrderGoodsResult(bill_uid).use_cookie_pool().get_result()
            return result
        except Exception as e:
            print('--------error traceback--------')
            print(traceback.format_exc())
            print(e)
            if retry > 0:
                retry -= 1
                time.sleep(25)
                return self.fetch_purchase_sku(bill_uid, retry)
            else:
                return {}

    def close_purchase_bill(self, bill_code='', level=1, bill_data='', bill_sku_data='', close_remark='', retry=3):
        """
        根据采购单据编码关闭采购订单;
        这个关闭的是第一层的采购订单（第一层指的是直接查询万里牛返回的面板信息）
        :param bill_code:
        :param level:
        :param bill_data:
        :param bill_sku_data:
        :param close_remark: 关闭备注
        :param retry: 重试次数
        :return:
        """
        print('关闭采购单: {}'.format(bill_code))
        try:
            if level == 1:
                result = PurchaseOrderClose() \
                    .set_param('bill_code', bill_code) \
                    .set_param('close_remark', close_remark) \
                    .get_result()
                result = json.loads(result)
                print('通过接口关闭采购单的结果: {}'.format(result))
                code = result.get('code')
                if code != 0:
                    if retry > 0:
                        return self.close_purchase_bill(bill_code, level, bill_data, bill_sku_data, close_remark,
                                                        retry - 1)
                    else:
                        # 发送关闭采购单失败的钉钉通知
                        title = '关闭采购单失败报警'
                        text = '关闭采购单失败了: {} 次, 需要手动去万里牛关闭异常订单: {}'.format(3, bill_code)
                        DingTalk(ROBOT_TOKEN, title, text).enqueue()
                return result.get('message')
            else:
                result = CloseAudit(bill_data, bill_sku_data).use_cookie_pool().get_result()
            return result
        except Exception as e:
            print('--------error traceback--------')
            print(traceback.format_exc())
            print('close_purchase_bill error: {}'.format(e))
            if retry > 0:
                return self.close_purchase_bill(bill_code, level, bill_data, bill_sku_data, close_remark, retry - 1)
            else:
                # 发送关闭采购单失败的钉钉通知
                title = '关闭采购单失败报警'
                text = '关闭采购单失败了: {} 次, 需要手动去万里牛关闭异常订单: {}'.format(3, bill_code)
                DingTalk(ROBOT_TOKEN, title, text).enqueue()
                return '关闭采购单失败，重试次数: {}'.format(retry)

    @staticmethod
    def compare_add_purchase(input_dict, crawl_dict, crawl_sku_dict):
        """
        比较两个dict数据是否一样
        :param input_dict:
        :param crawl_dict:
        :param crawl_sku_dict:
        :return:
        """
        lack_data = set()
        if len(input_dict.get('list')) > len(crawl_sku_dict):
            lack_data.add('传入的list大小比抓取的list数量大，有问题')
            return 1, lack_data
        for _input in input_dict.get('list'):
            for index, _sku in enumerate(crawl_sku_dict):
                if _input['skuBarcode'] == _sku.get('spec_code') and int(_input['purchaseCount']) == int(
                        _sku.get('pchs_size')) and _input['storageName'] == crawl_dict.get('storage_name'):
                    break
                if _input['skuBarcode'] != _sku.get('spec_code') and index == len(crawl_sku_dict) - 1:
                    lack_data.add('skuBarcode')
                if _input['purchaseCount'] != int(_sku.get('pchs_size')) and index == len(crawl_sku_dict) - 1:
                    lack_data.add('purchaseCount')
                # if _input['supplierName'] != crawl_dict.get('supplier_name'):
                #     lack_data.add('supplierName')
                if _input['storageName'] != crawl_dict.get('storage_name'):
                    lack_data.add('storageName')
        if lack_data:
            return 1, lack_data
        else:
            return 0, ''

    @staticmethod
    def send_call_back_msg(data, err_msg='', data_id='', status=1, erp_purch_no=''):
        """
        发送返回的消息数据
        :return:
        """
        data = deepcopy(data)
        return_msg = {
            "code": status,  # 0：成功 1：失败
            "errMsg": err_msg,  # 如果code为1，请将失败的具体原因返回
            "tgPurchaseNo": data.get('list')[0].get('purchaseNo'),
            "erpPurchaseNo": "",
            "warehouseId": data.get('warehouseId'),
            "type": data.get('type'),
            "list": data.get('list')
        }
        print('发送返回的消息数据: before: {}'.format(return_msg))
        tg_purchase_no = str(return_msg['tgPurchaseNo'])
        if not tg_purchase_no:
            return_msg['errMsg'] = return_msg['errMsg'] + '传入的tgPurchaseNo为空'

        storage_code = data.get('list')[0].get('storageCode', '')
        if not storage_code:
            return_msg['errMsg'] = return_msg['errMsg'] + '传入的storageCode为空'

        if status == 0 and tg_purchase_no and storage_code:
            # 设置本天鸽单号为已发送状态
            default_storage_redis.set("{}:{}:{}".format(tg_purchase_no, storage_code, data.get("isSecond", False)),
                                      erp_purch_no,
                                      30 * 24 * 3600)
            return_msg['erpPurchaseNo'] = erp_purch_no
        # 发送失败的消息
        if status != 0 and Helper.in_project_env():
            # 发送失败的消息
            title = '万里牛采购订单同步(添加)操作失败'
            ding_msg = '万里牛采购订单同步(添加)操作失败详情: {}, 天鸽采购单号: {}'.format(err_msg, tg_purchase_no)
            DingTalk(HUPUN_SYNC_ABNORMAL_ROBOT, title, ding_msg).enqueue()
            # 同时发送邮件通知
            if data.get('email'):
                EmailSender() \
                    .set_receiver(data.get('email')) \
                    .set_mail_title(title) \
                    .set_mail_content(ding_msg) \
                    .send_email()

        # 发送返回的消息
        print('发送返回的消息数据: {}'.format(return_msg))

        from mq_handler import CONST_MESSAGE_TAG_PURCHARSE_ADD_RE
        from mq_handler import CONST_ACTION_UPDATE
        from pyspider.libs.mq import MQ
        return_date = Date.now().format()
        msg_tag = CONST_MESSAGE_TAG_PURCHARSE_ADD_RE
        MQ().publish_message(msg_tag, return_msg, data_id, return_date, CONST_ACTION_UPDATE)

    @staticmethod
    def sended_success_msg(tg_purchase_no, storage_code, is_second):
        """
        判断redis里的天鸽采购单号的状态是否为已发送
        现在一个天鸽采购单可以对应多个仓库(线下总仓和线上总仓)，所以需要把这两个值一起作为key
        :param tg_purchase_no: 天鸽采购单
        :param storage_code: 仓库ID
        :param is_second: 是否是采购单70%、30%分批同步的第二批同步
        :return: bill_code: 成功添加采购单生成的erp采购单
        """
        return default_storage_redis.get("{}:{}:{}".format(tg_purchase_no, storage_code, is_second))

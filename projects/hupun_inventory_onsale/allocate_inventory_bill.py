import gevent.monkey
gevent.monkey.patch_ssl()
from hupun_inventory_onsale.page.check_allocate_inventory import CheckAllocateInventory
from hupun_inventory_onsale.page.query_allocate_inventory import QueryAllocateInventory
from mq_handler.base import Base
from pyspider.helper.date import Date
from hupun_inventory_onsale.on_shelf_config import *
import traceback
from pyspider.helper.retry import Retry
from alarm.page.ding_talk import DingTalk
import random
import requests
import json
from hupun_inventory_onsale.es.allocate_bill import EsAllocateBill


class AllocateInvBill(Base):
    '''
    创建并审核库存调拨单
    '''

    def execute(self):
        print('开始创建并审核调拨单')
        self.print_basic_info()
        data = self._data

        try:
            add_res = self.add_allocate_bill(data)
            if add_res[0] is True:
                # 调拨单成功生成，保存该单
                self.save_allocate_bill(self._data, add_res[1])
                query_res = self.query_allocate(add_res[1])
                if query_res[0] is True:
                    check_res = self.check_allocate(query_res[1])
                    if check_res[0] is True:
                        print('=====已完成库存调拨单的生成和审核======')
                    else:
                        self.ding_talk_alarm(check_res[1], add_res[1])
                        print('审核库存调拨单失败')
                else:
                    self.ding_talk_alarm(query_res[1], add_res[1])
                    print('查询库存调拨单失败')
            else:
                self.ding_talk_alarm(add_res[1])
                print('生成库存调拨单失败')
        except:
            print(traceback.format_exc())
            self.ding_talk_alarm('未被捕捉到的生成或审核调拨单失败')
            print('=====未正确生成或审核库存调拨单=====')

    @Retry.retry_parameter(2, sleep_time=5)
    def add_allocate_bill(self, data):
        print(Date.now().format(), '开始调创建调拨单api')
        try:
            if not data.get('bill_type', ''):
                data['bill_type'] = 1
            if not data.get('oper_nick', ''):
                data['oper_nick'] = 'aipc1@yourdream.cc'
            if not data.get('remark', ''):
                data['remark'] = 'it自动创建的调拨单'
            self._data = data
            url = ERP_ADD_ALLOCATE_URL
            add_allocate_json = requests.post(url, data=json.dumps(data),
                                                headers={'Content-Type': 'application/json'},
                                                timeout=30).json()
            if add_allocate_json.get('code', '') == 0 and add_allocate_json.get('data', ''):
                res = add_allocate_json.get('data', '')
                return True, res
            else:
                error_msg = '调用API增加调拨单失败，' + add_allocate_json.get('message', '') \
                    if add_allocate_json.get('message', '') else '调用API增加调拨单失败'
                return 'other', error_msg
        except Exception as e:
            print(traceback.format_exc())
            return False, '调用api发生异常错误'

    @Retry.retry_parameter(5, sleep_time=61, rate=0.02)
    def query_allocate(self, bill_code):
        cookie_position = random.randint(3, 7)
        res = QueryAllocateInventory(bill_code).set_cookie_position(cookie_position).use_cookie_pool().get_result()
        return res

    @Retry.retry_parameter(5, sleep_time=61, rate=0.02)
    def check_allocate(self, bill_uid):
        cookie_position = random.randint(3, 7)
        res = CheckAllocateInventory(bill_uid).set_cookie_position(cookie_position).use_cookie_pool().get_result()
        return res

    @staticmethod
    def ding_talk_alarm(error_msg, bill_code=''):
        token = '87053027d1d9c2ca35b1eda6d248b3d087b764c135f1cb9b1b3387c47322d411'
        title = '生成库存调拨单操作报警'
        bill_msg = '库存调拨单：' + bill_code if bill_code else ''
        content = bill_msg + '生成或审核库存调拨单失败，原因：' + error_msg
        DingTalk(token, title, content).enqueue()

    def save_allocate_bill(self, data, bill_code):
        data['bill_code'] = bill_code
        data['syncTime'] = Date.now().format_es_utc_with_tz()
        EsAllocateBill().update([data], async=True)

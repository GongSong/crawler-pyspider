import uuid
from copy import deepcopy
import json
from hupun_api.page.base import *


class AppointmentOutbound(Base):
    PATH = '/erp/stock/out/requestbill/add'
    """
    新增 预约出库单 api
    """

    def __init__(self, to_next_page=False, post_data=None):
        super(AppointmentOutbound, self).__init__(self.PATH, post_data)
        self.__to_next_page = to_next_page

    def set_page(self, page):
        self.set_param('page', page)
        return self

    def set_page_size(self, page_size):
        self.set_param('limit', page_size)
        return self

    def parse_response(self, response, task):
        result = response.text
        msg = {
            'data': self._post_data,
        }
        self.send_message(msg, md5string(uuid.uuid4()))
        return result

    def get_unique_define(self):
        return uuid.uuid4()


if __name__ == '__main__':
    js_data = {
        'storage_code': '020',
        'remark': '自动同步万里牛',
        'reason': "线下门店商品配送",
        'address': "上海五角场",
        'mobile': "15945678901",
        'receiver': "杨千里",
        'details': [
            {
                'size': 4,
                'spec_code': '19490F0003R304',
            },
            {
                'size': 5,
                'spec_code': '1952D00050W172',
            }
        ]
    }
    result = AppointmentOutbound().set_param('bill', js_data).get_result()
    print(result)
    ss = json.loads(result).get("data", "")
    print(ss)

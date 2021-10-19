import uuid
from copy import deepcopy

from hupun_api.page.base import *


class OutboundOrder(Base):
    PATH = '/erp/stock/out/stockbill/add'
    """
    新增 出库单（只能直接出库）api
    """

    def __init__(self, to_next_page=False, post_data=None):
        super(OutboundOrder, self).__init__(self.PATH, post_data)
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
        'remark': '自动同步万里牛,收货单：DBRK202006280002',
        'reason': "线下门店商品配送",
        'details': [
            {
                'size': 2,
                'spec_code': '2020A00057W305',
            },
            {
                'size': 2,
                'spec_code': '2020D00018W502',
            }
        ]
    }
    result = OutboundOrder().set_param('bill', js_data).get_result()
    print('result: {}'.format(result))
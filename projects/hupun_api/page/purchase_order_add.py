import uuid
from copy import deepcopy

from hupun_api.page.base import *


class PurchaseOrderAdd(Base):
    PATH = '/erp/purchase/purchasebill/add'
    """
    采购订单 的数据新增
    """

    def __init__(self, to_next_page=False, post_data=None):
        super(PurchaseOrderAdd, self).__init__(self.PATH, post_data)
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

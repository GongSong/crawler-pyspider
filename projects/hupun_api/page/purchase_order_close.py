import uuid
from copy import deepcopy

from hupun_api.page.base import *
from pyspider.helper.string import merge_str


class PurchaseOrderClose(Base):
    PATH = '/erp/purchase/purchasebill/close'
    """
    采购订单 的关闭
    """

    def __init__(self, post_data=None):
        super(PurchaseOrderClose, self).__init__(self.PATH, post_data)
        self.__unique_name = 'purchase_bill_cloase'

    def set_page(self, page):
        self.set_param('page', page)
        return self

    def set_page_size(self, page_size):
        self.set_param('limit', page_size)
        return self

    def parse_response(self, response, task):
        result = response.text
        self.send_message({
            'result': result,
            'post_data': self._post_data,
            'unique_name': self.__unique_name
        }, md5string(merge_str(self._post_data.get('bill_code', ''), self.__unique_name)))
        return result

    def get_unique_define(self):
        return uuid.uuid4()

import uuid
from copy import deepcopy

from hupun_api.page.base import *


class PurchaseOrder(Base):
    PATH = '/erp/purchase/purchasebill/query'
    """
    采购订单 的数据抓取
    """

    def __init__(self, to_next_page=False, post_data=None):
        super(PurchaseOrder, self).__init__(self.PATH, post_data)
        self.__to_next_page = to_next_page

    def set_page(self, page):
        self.set_param('page', page)
        return self

    def set_page_size(self, page_size):
        self.set_param('limit', page_size)
        return self

    def parse_response(self, response, task):
        result = response.text
        inner_data = result['data']
        if inner_data:
            self.crawl_next_page()
        return {
            'unique_name': 'purchase_order_api',
            'result': result
        }

    def get_unique_define(self):
        return uuid.uuid4()

    def crawl_next_page(self):
        """
        抓取下一页
        :return:
        """
        post_data = deepcopy(self._post_data)
        post_data['page'] = post_data['page'] + 1
        if self.__to_next_page:
            self.crawl_handler_page(PurchaseOrder(to_next_page=self.__to_next_page, post_data=post_data))

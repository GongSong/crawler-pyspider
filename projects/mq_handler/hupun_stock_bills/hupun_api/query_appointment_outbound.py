import uuid
from copy import deepcopy

from hupun_api.page.base import *


class QueryAppointmentOutboundApi(Base):
    PATH = '/erp/stock/out/requestbill/query'
    """
    查询 预约出库单 api
    """

    def __init__(self, to_next_page=False, post_data=None):
        super(QueryAppointmentOutboundApi, self).__init__(self.PATH, post_data)
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
    stock_request_code = "SO202006290005"

    result = QueryAppointmentOutboundApi().set_param('stock_request_code', stock_request_code).set_page(1).set_page_size(2).get_result()
    print(result)


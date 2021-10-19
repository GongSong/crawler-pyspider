import uuid
import json
from hupun_api.page.base import *


class CloseAppointmentReceipt(Base):
    PATH = '/erp/stock/in/requestbill/close'
    """
    关闭 预约入库单 api
    """

    def __init__(self, to_next_page=False, post_data=None):
        super(CloseAppointmentReceipt, self).__init__(self.PATH, post_data)
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
    stock_request_code = "EO202009080009"
    result = CloseAppointmentReceipt().set_param('stock_request_code', stock_request_code).get_result()
    print(result)
    ss = json.loads(result).get("data", "")
    print(ss)

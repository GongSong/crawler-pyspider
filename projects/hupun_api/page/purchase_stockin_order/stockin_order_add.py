import uuid

from hupun_api.page.base import *


class StockinOrderAdd(Base):
    PATH = '/erp/purchase/purchasestockbill/add'
    """
    采购入库单API 的数据添加
    接口的参数一定要传remark（备注），不然就会失败
    """

    def __init__(self):
        super(StockinOrderAdd, self).__init__(self.PATH)

    def parse_response(self, response, task):
        result = response.text
        return result

    def get_unique_define(self):
        return uuid.uuid4()

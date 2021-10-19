import json
import uuid
from copy import deepcopy

from hupun_api.model.es.order_api import OrderApiEs
from hupun_api.page.base import *


class OrderApi(Base):
    PATH = '/erp/opentrade/query/trades'
    """
    订单API 的数据抓取
    """

    def __init__(self, to_next_page=False, post_data=None):
        super(OrderApi, self).__init__(self.PATH, post_data)
        self.__to_next_page = to_next_page

    def get_unique_define(self):
        return uuid.uuid4()

    def parse_response(self, response, task):
        result = response.text
        inner_data = json.loads(result)['data']
        if len(inner_data) > 0:
            sync_time = Date.now().format_es_utc_with_tz()
            for _data in inner_data:
                _data['sync_time'] = sync_time
            OrderApiEs().update(inner_data, async=True)
            self.crawl_next_page()
        return {
            'post_data': self._post_data,
            'content length': len(response.content),
            'unique_name': 'order_api_result',
            'result': result
        }

    def crawl_next_page(self):
        """
        抓取下一页
        :return:
        """
        post_data = deepcopy(self._post_data)
        post_data['page'] = post_data['page'] + 1
        if self.__to_next_page:
            self.crawl_handler_page(OrderApi(to_next_page=self.__to_next_page, post_data=post_data))

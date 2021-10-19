import json
import uuid
from copy import deepcopy

from hupun_api.model.es.goods_inventory import GoodsInventoryApi as InvenApiEs
from hupun_api.page.base import *
from pyspider.helper.string import merge_str


class InventoryApi(Base):
    PATH = '/erp/open/inventory/items/get/by/modifytime'
    """
    库存 API 的数据抓取
    """

    def __init__(self, to_next_page=False, post_data=None):
        super(InventoryApi, self).__init__(self.PATH, post_data)
        self.__to_next_page = to_next_page

    def set_page(self, page):
        self.set_param('page_no', page)
        return self

    def set_page_size(self, page_size):
        self.set_param('page_size', page_size)
        return self

    def parse_response(self, response, task):
        result = response.text
        inner_data = json.loads(result).get('data', [])
        if len(inner_data) > 0:
            sync_time = Date.now().format_es_utc_with_tz()
            for _data in inner_data:
                _data['sync_time'] = sync_time
                self.send_message(_data, merge_str('inventory_api',
                                                   _data.get('goods_code', ''),
                                                   _data.get('sku_code', '')))
            InvenApiEs().update(inner_data, async=True)
            self.crawl_next_page()
        return {
            'post_data': self._post_data,
            'content length': len(response.content),
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
        post_data['page_no'] = post_data['page_no'] + 1
        if self.__to_next_page:
            self.crawl_handler_page(InventoryApi(to_next_page=self.__to_next_page, post_data=post_data))

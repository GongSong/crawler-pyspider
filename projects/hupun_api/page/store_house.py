import uuid
from copy import deepcopy

from hupun_api.page.base import *


class StoreHouse(Base):
    PATH = '/erp/base/storage/query'
    """
    仓库 的数据抓取
    """

    def __init__(self, to_next_page=False, post_data=None):
        super(StoreHouse, self).__init__(self.PATH, post_data)
        self.__to_next_page = to_next_page

    def set_page(self, page):
        self.set_param('page', page)
        return self

    def set_page_size(self, page_size):
        self.set_param('limit', page_size)
        return self

    def parse_response(self, response, task):
        # if self.__to_next_page:

        result = response.text
        print('result: {}'.format(result))
        return
        inner_data = result['data']
        if inner_data:
            print('inner_data: {}'.format(inner_data))
            # self.crawl_next_page()
        else:
            return {
                'msg': '没有数据了',
                'post_data': self._post_data,
                'content length': len(response.content),
                'content': response.content
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
        self.crawl_handler_page(StoreHouse(to_next_page=self.__to_next_page, post_data=post_data))
        pass
        # if self._post_data:
        #     page_no = int(self._post_data['page_no'])
        #     self._post_data['page_no'] = page_no + 1
        # if self.__to_next_page and not self.check_flag(self.CONST_FLAG_BREAK) and self.in_processor():
        #     self.crawl_handler_page(Inventory(self.__path,
        #                                       self._post_data,
        #                                       self.__to_next_page))

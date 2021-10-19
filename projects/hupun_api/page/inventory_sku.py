import uuid
from hupun_api.page.base import *


class InventorySku(Base):
    """
    库存sku 的数据抓取
    """

    def __init__(self, path, post_data=None, to_next_page=False):
        super(InventorySku, self).__init__(path, post_data)
        self.__path = path
        self.__to_next_page = to_next_page

    def parse_response(self, response, task):
        result = response.text
        print('result: {}'.format(result))
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
        pass
        # if self._post_data:
        #     page_no = int(self._post_data['page_no'])
        #     self._post_data['page_no'] = page_no + 1
        # if self.__to_next_page and not self.check_flag(self.CONST_FLAG_BREAK) and self.in_processor():
        #     self.crawl_handler_page(Inventory(self.__path,
        #                                       self._post_data,
        #                                       self.__to_next_page))

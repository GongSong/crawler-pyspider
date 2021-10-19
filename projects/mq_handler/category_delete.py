from hupun.page.category.goods_categories_delete import GoodsCategoryDelete
from mq_handler.base import Base
from pyspider.helper.date import Date


class CategoryDelete(Base):
    """
    删除erp的类目数据
    """

    def execute(self):
        print('consume category delete operation')
        self.print_basic_info()
        data = self._data
        uid = data.get('erpGoodsCategoryId', [])
        # 写入数据
        for _u in uid:
            GoodsCategoryDelete(data, self._data_id, _u) \
                .set_priority(GoodsCategoryDelete.CONST_PRIORITY_BUNDLED) \
                .set_cookie_position(1) \
                .enqueue()

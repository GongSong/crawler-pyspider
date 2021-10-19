from hupun.page.category.goods_categories_drag import GoodsCategoryDrag
from mq_handler.base import Base
from pyspider.helper.date import Date


class CategoryDrag(Base):
    """
    拖拽erp的类目数据
    """

    def execute(self):
        print('category operation drag data')
        self.print_basic_info()
        data = self._data
        # 写入数据
        uid = data.get('erpGoodsCategoryId', '')
        parent_id = data.get('erpParentId', '')
        name = data.get('name', '')
        GoodsCategoryDrag(uid, parent_id, name) \
            .set_priority(GoodsCategoryDrag.CONST_PRIORITY_BUNDLED) \
            .set_cookie_position(1) \
            .enqueue()

from pyspider.core.model.es_base import *


class BasProductColorEs(Base):
    """
    澜东云 颜色档案 的数据
    """

    def __init__(self):
        super(BasProductColorEs, self).__init__()
        self.cli = es_cli
        self.index = 'pylandong_bas_product_color'
        self.test_index = 'pylandong_bas_product_color_test'
        self.doc_type = 'data'
        self.primary_keys = ['UUID']

    def get_all_bas_color(self):
        """
        获取所有的颜色档案
        :return:
        """
        return self.scroll(EsQueryBuilder())

    def get_bas_color_by_names(self, color_names):
        """
        通过颜色名称列表拿到颜色内容
        :param color_names:
        :return:
        """
        return EsQueryBuilder().terms("ColorName", color_names).search(self, 1, 1000).get_list()


if __name__ == '__main__':
    BasProductColorEs().create_table()

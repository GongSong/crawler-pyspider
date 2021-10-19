from pyspider.core.model.es_base import *


class BasBrandEs(Base):
    """
    澜东云 波段档案 的数据
    """

    def __init__(self):
        super(BasBrandEs, self).__init__()
        self.cli = es_cli
        self.index = 'pylandong_bas_brand'
        self.test_index = 'pylandong_bas_brand_test'
        self.doc_type = 'data'
        self.primary_keys = ['UUID']

    def get_all_bas_brand(self):
        """
        获取所有的波段档案
        :return:
        """
        return self.scroll(EsQueryBuilder())

    def get_band_item_by_name(self, band_name):
        """
        通过波段名称拿到波段内容
        :param band_name:
        :return:
        """
        band_code = {}
        builder = EsQueryBuilder().term("DataName", band_name).search(self, 1, 100)
        if builder.get_count() > 0:
            band_code = builder.get_one()
        return band_code


if __name__ == '__main__':
    BasBrandEs().create_table()

from pyspider.core.model.es_base import *


class MassPatternDesignEs(Base):
    """
    澜东云 商品档案 的数据
    """

    def __init__(self):
        super(MassPatternDesignEs, self).__init__()
        self.cli = es_cli
        self.index = 'pylandong_mass_pattern_design'
        self.test_index = 'pylandong_mass_pattern_design_test'
        self.doc_type = 'data'
        self.primary_keys = ['UUID']

    def get_all_pattern_design(self):
        """
        获取所有的商品档案
        :return:
        """
        return self.get_scroll_dict("UUID", ["UUID", "DesignCode", "UpdateOn"])


if __name__ == '__main__':
    MassPatternDesignEs().create_table()

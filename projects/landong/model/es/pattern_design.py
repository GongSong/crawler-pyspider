from pyspider.core.model.es_base import *


class PatternDesignEs(Base):
    """
    澜东云 新款档案 的数据
    """

    def __init__(self):
        super(PatternDesignEs, self).__init__()
        self.cli = es_cli
        self.index = 'pylandong_pattern_design'
        self.test_index = 'pylandong_pattern_design_test'
        self.doc_type = 'data'
        self.primary_keys = ['UUID']

    def get_all_pattern_design(self):
        """
        获取所有的 新款档案
        :return:
        """
        return self.scroll(EsQueryBuilder())


if __name__ == '__main__':
    PatternDesignEs().create_table()

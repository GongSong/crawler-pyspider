from pyspider.core.model.es_base import *


class BasPatternSizeEs(Base):
    """
    澜东云 尺码档案 的数据
    """

    def __init__(self):
        super(BasPatternSizeEs, self).__init__()
        self.cli = es_cli
        self.index = 'pylandong_bas_pattern_size'
        self.test_index = 'pylandong_bas_pattern_size_test'
        self.doc_type = 'data'
        self.primary_keys = ['UUID']

    def get_all_pattern_size(self):
        """
        获取所有的尺码档案
        :return:
        """
        return self.get_scroll_dict("UUID", ["UUID", "DataCode", "DataName", "Enabled", "UpdateOn"])

    def get_all_size(self):
        """
        获取所有尺码档案的尺码编码，名称
        :return:
        """
        data = self.get_scroll_list(["DataCode", "DataName"])
        size_code_data = []
        size_name_data = []
        for _ in data:
            size_code_data.append(_.get("DataCode"))
            size_name_data.append(_.get("DataName"))
        return size_code_data, size_name_data

    def get_size_by_name(self, name_list):
        """
        根据尺码名列表获取尺码详情
        :param name_list:
        :return:
        """
        return EsQueryBuilder().terms("DataName", name_list).search(self, 1, 1000).get_list()


if __name__ == '__main__':
    BasPatternSizeEs().create_table()

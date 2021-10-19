from pyspider.core.model.es_base import *


class BasProductCategoryEs(Base):
    """
    澜东云 品类档案 的数据
    """

    def __init__(self):
        super(BasProductCategoryEs, self).__init__()
        self.cli = es_cli
        self.index = 'pylandong_bas_product_category'
        self.test_index = 'pylandong_bas_product_category_test'
        self.doc_type = 'data'
        self.primary_keys = ['UUID']

    def get_all_pattern_category(self):
        """
        获取所有的品类档案
        :return:
        """
        return self.get_scroll_dict("UUID", ["UUID", "CategoryCode", "CategoryName", "Enabled", "UpdateOn", "ParentId"])

    def get_all_category(self):
        """
        获取所有品类档案的品类编码，名称
        :return:
        """
        data = self.get_scroll_list(["CategoryCode", "CategoryName"])
        category_code_data = []
        category_name_data = []
        for _ in data:
            category_code_data.append(_.get("CategoryCode"))
            category_name_data.append(_.get("CategoryName"))
        return category_code_data, category_name_data

    def get_category_code_map(self):
        """
        获取所有的品类 code 和 UUID 的 map
        :return:
        """
        data = self.get_scroll_list(["UUID", "CategoryCode"])
        return {item.get("UUID", ""): item.get("CategoryCode", "") for item in data}

    def get_category_by_name(self, category_name):
        """
        根据类目名获取类目详情
        :param category_name:
        :return:
        """
        category = {}
        builder = EsQueryBuilder().term("CategoryName", category_name).search(self, 1, 1000)
        if builder.get_count() > 0:
            category = builder.get_one()
        return category


if __name__ == '__main__':
    BasProductCategoryEs().create_table()

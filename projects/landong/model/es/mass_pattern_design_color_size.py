from pyspider.core.model.es_base import *


class MassPatternDesignColorSizeEs(Base):
    """
    澜东云 商品档案-商品编码 的数据
    """

    def __init__(self):
        super(MassPatternDesignColorSizeEs, self).__init__()
        self.cli = es_cli
        self.index = 'pylandong_mass_pattern_design_color_size'
        self.test_index = 'pylandong_mass_pattern_design_color_size_test'
        self.doc_type = 'data'
        self.primary_keys = ['UUID']

    def get_all_pattern_design_color_size(self, mass_code):
        """
        获取当前商品的商品编码
        :return:
        """
        return self.get_scroll_dict("UUID", ["UUID"], EsQueryBuilder().term("MassCode", mass_code))

    def mass_code_get_sku(self, mass_code, deleted=False):
        """
        根据MassCode获取SKU
        :param mass_code:
        :param deleted: 是否已删除
        :return:
        """
        sku_data = self.scroll(EsQueryBuilder().term("MassCode", mass_code).term("deleted", deleted))
        sku_map = {}
        sku_list = []
        for item in sku_data:
            for _ in item:
                if _.get("SKU"):
                    sku_list.append(_.get("SKU"))
                    sku_map.setdefault(_.get("SKU"), _)
        return sku_list, sku_map


if __name__ == '__main__':
    MassPatternDesignColorSizeEs().create_table()

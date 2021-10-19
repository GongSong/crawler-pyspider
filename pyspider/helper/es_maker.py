from helper.es_query_builder import EsQueryBuilder
from helper.utils import add_prefix
from model.hupun.goods_category import GoodsCategory


def add_filter(es_builder: EsQueryBuilder, filter_dict: dict):
    for key, value in filter_dict.items():
        if value == '':
            value = None
        if type(value) == dict:
            start = value.get('start') if not value.get('start') == '' else None
            end = value.get('end') if not value.get('end') == '' else None
            es_builder.range_e(key, start, end)
        elif type(value) == list:
            es_builder.terms(key, value if not value == [] else None)
        else:
            if key == 'categoryId':
                for k, v in GoodsCategory().get_category_names(value, False).items():
                    if len(v):
                        es_builder.term(add_prefix(k, 'erp'), v)
            elif key == 'erpBarcode' and value is not None:
                es_builder.mysql_fuzzy('erpBarcode', value)
            else:
                es_builder.term(key, value if not value == '' else None)
    return es_builder

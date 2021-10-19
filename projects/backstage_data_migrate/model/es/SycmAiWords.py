from pyspider.core.model.es_base import *


class SycmAiWords(Base):
    """
    生意参谋 后台搜索词
    """

    def __init__(self):
        super(SycmAiWords, self).__init__()
        self.cli = es_cli
        self.index = 'tmall_tag'
        self.doc_type = 'data'
        self.primary_keys = ['date', 'category', 'keyType', 'key']

    def get_today_data_sum(self, today_str):
        count = EsQueryBuilder() \
            .term('date', today_str) \
            .search(self, 1, 0) \
            .get_count()
        return count

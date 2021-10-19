from pyspider.core.model.es_base import *


class FashionWords(Base):
    """
    图片爬虫
    """
    def __init__(self):
        super(FashionWords, self).__init__()
        self.cli = es_cli
        self.index = 'fashion_words'
        self.test_index = 'fashion_words'
        self.doc_type = 'data'
        self.primary_keys = 'contentId'

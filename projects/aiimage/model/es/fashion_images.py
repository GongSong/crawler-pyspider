from pyspider.core.model.es_base import *
from pyspider.helper.date import Date


class FashionImages(Base):
    """
    图片爬虫
    """
    def __init__(self):
        super(FashionImages, self).__init__()
        self.cli = es_cli
        self.index = 'fashion_images'
        self.test_index = 'fashion_images_test'
        self.doc_type = 'data'
        self.primary_keys = 'imageId'

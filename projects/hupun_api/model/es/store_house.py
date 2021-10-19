from pyspider.core.model.es_base import *


class StoreHouse(Base):
    """
    万里牛 仓库 标签的数据
    """

    def __init__(self):
        super(StoreHouse, self).__init__()
        self.cli = es_cli
        self.index = 'hupun_storehouse_data'
        self.test_index = 'pyhupun_storehouse_data_test'
        self.doc_type = 'data'
        self.primary_keys = 'storageUid'

    def get_storage(self, page_size=200):
        """
        获取不同渠道的所有商品
        :param page_size: 页码大小
        :return:
        """
        storage_list = []
        results = self.scroll(page_size=page_size)
        for item in results:
            for _ in item:
                storage_code = _['storageCode']
                storage_list.append(storage_code)
        return storage_list

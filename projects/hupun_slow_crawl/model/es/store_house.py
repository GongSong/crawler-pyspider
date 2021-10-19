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

    def get_storage_ids(self):
        store_list = EsQueryBuilder().search(self, 1, 100).get_list()
        return [_['storageUid'] for _ in store_list]

    def get_storage_ids_map(self) -> dict:
        store_list = EsQueryBuilder().search(self, 1, 100).get_list()
        return {_['storageUid']: _['storageName'] for _ in store_list}

    def get_uid_by_name(self, name):
        """
        根据仓库名称获取仓库名的uid
        :param name:
        :return:
        """
        uid = EsQueryBuilder().term('storageName.keyword', name).search(self, 1, 100).get_one()
        return uid.get('storageUid')

    def get_name_by_uid(self, uid):
        """
        根据仓库名的uid获取仓库名称
        :param uid:
        :return:
        """
        uid = EsQueryBuilder().term('storageUid.keyword', uid).search(self, 1, 100).get_one()
        return uid.get('storageName')

    def get_uid_and_name_by_code(self, code):
        """
        根据仓库编码获取仓库名的uid
        :param code:
        :return:
        """
        uid = EsQueryBuilder().term('storageCode.keyword', code).search(self, 1, 100).get_one()
        return uid.get('storageUid'), uid.get('storageName')

    def get_storage_type_by_code(self, code):
        """
        根据仓库编码获取仓库名的 storageType
        :param code:
        :return:
        """
        uid = EsQueryBuilder().term('storageCode.keyword', code).search(self, 1, 100).get_one()
        return uid.get('storageType')

    def get_all_name_uid_dict(self):
        '''
        获取所有的仓库名和对应仓库uid的字典
        :return: dict
        '''
        storage_dict = {}
        store_list = EsQueryBuilder().search(self, 1, 100).get_list()
        for item in store_list:
            storage_dict[item['storageName']] = item['storageUid']
        return storage_dict
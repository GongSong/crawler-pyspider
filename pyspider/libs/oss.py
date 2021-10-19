import os

import oss2
from pyspider.config import config


class Oss:
    CONST_TALENT_PATH = 'crawler/table/talent/'
    CONST_SYCM_PATH = 'crawler/table/'
    CONST_JD_FLOW_PATH = 'crawler/table/flow/京东/'  # 京东流量数据
    CONST_JD_GOODS_PATH = 'crawler/table/京东/'  # 京东商品明细
    CONST_SYCM_FLOW_PATH = 'crawler/table/flow/生意参谋/'  # 生意参谋的流量来源数据文件下载
    CONST_SYCM_TABLE_FLOW = 'crawler/table/flow/'  # 生意参谋天猫全量商品每周每月的流量数据下载
    CONST_SYCM_SHOP_PATH = 'crawler/table/shop/'
    CONST_SYCM_GOODS_FLOW_PATH = 'crawler/table/shop/each_goods/'
    CONST_TAOBAO_ACCOUNT_PATH = 'crawler/table/淘宝后台订单/'
    CONST_TAOBAO_MANAGER_SOFT_PATH = 'crawler/table/掌柜软件/'  # 天猫商品的类目、商品ID、商品货号等信息
    CONST_REDBOOK_DATA_PATH = 'crawler/table/小红书/'
    CONST_WEIPINHUI_PATH = 'crawler/table/weipinhui/'
    CONST_TMALL_GOODS_PATH = 'crawler/goods/tmall/'  # 天猫商品的json数据
    CONST_SYCM_GOODS_TRAFFIC_SOURCES = 'crawler/download_file/'  # 生意参谋每个icy商品的 流量来源流量数据下载
    # hupun
    CONST_IN_SALE_STORE_PATH = 'crawler/table/hupun/进销存报表/'
    # 这个上传到了图片bucket
    CONST_AI_IMAGE = 'crawler/ai/image/'
    CONST_BLOG_IMAGE = 'crawler/blog/image/'
    CONST_LANDONG_IMAGE = 'crawler/landong/image/'

    def __init__(self, access_key_id, access_key_secret, bucket_name, endpoint):
        self.__access_key_id = access_key_id
        self.__access_key_secret = access_key_secret
        self.__bucket_name = bucket_name
        self.__endpoint = endpoint
        self.__bucket = oss2.Bucket(
            oss2.Auth(self.__access_key_id, self.__access_key_secret),
            self.__endpoint,
            self.__bucket_name
        )

    def is_had(self, key):
        return self.__bucket.object_exists(key)

    def upload_data(self, key, data):
        self.__bucket.put_object(key, data)

    def upload_from_file(self, key, filename):
        self.__bucket.put_object_from_file(key, filename)

    def get_object(self, key):
        return self.__bucket.get_object(key)

    def get_data(self, key):
        return self.get_object(key).read()

    def to_locale_file(self, key, filename):
        return self.__bucket.get_object_to_file(key, filename)

    def list_objects(self, prefix='', file_path='', continuation_token="", max_keys=100):
        obj = self.__bucket.list_objects_v2(prefix=prefix, delimiter=file_path, continuation_token=continuation_token, max_keys=max_keys)
        obj_list = obj.object_list
        next_token = obj.next_continuation_token
        return obj_list, next_token

    def keys(self, prefix, page_size=1000):
        """
        根据前缀罗列Bucket里的文件
        :param prefix: 文件名的前缀
        :param page_size: 返回的页码大小
        :return:
        """
        paths = self.__bucket.list_objects(prefix=prefix, max_keys=page_size)
        while True:
            next_marker = paths.next_marker
            obj_list = paths.object_list
            yield paths
            paths = self.__bucket.list_objects(prefix=prefix, marker=next_marker, max_keys=page_size)
            if len(obj_list) < page_size:
                break

    @staticmethod
    def get_key(path, *paths):
        return os.path.join(path, *paths)


oss = Oss(config.get('oss', 'access_key_id'),
          config.get('oss', 'access_key_secret'),
          config.get('oss', 'bucket_name'),
          config.get('oss', 'endpoint'))

oss_cdn = Oss(config.get('oss_cdn', 'access_key_id'),
              config.get('oss_cdn', 'access_key_secret'),
              config.get('oss_cdn', 'bucket_name'),
              config.get('oss_cdn', 'endpoint'))

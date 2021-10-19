from crawl_taobao_goods_migrate.model.es.es_based_spu_summary import EsBasedSpuSummary
from pyspider.libs.utils import md5string

from pyspider.core.model.mongo_base import *


class Task(TaskBase):
    def __init__(self):
        super(Task, self).__init__()

    @staticmethod
    def get_task_id(name, key):
        return md5string(name + key)

    @staticmethod
    def get_task_id_goods_detail(goods_id):
        return Task.get_task_id('goods_details', goods_id)

    @staticmethod
    def get_task_id_goods_image(goods_id):
        return Task.get_task_id('goods_image', goods_id)

    @staticmethod
    def get_task_id_goods_shelf(goods_id):
        return Task.get_task_id('goods_shelf', goods_id)

    @staticmethod
    def get_task_id_shop_details(shop_id):
        return Task.get_task_id('shop_details', shop_id)

    @staticmethod
    def get_task_id_shop_goods(shop_id):
        return Task.get_task_id('shop_goods', shop_id)

    @staticmethod
    def get_task_id_goods_rate(goods_id):
        return Task.get_task_id('goods_rate', goods_id)




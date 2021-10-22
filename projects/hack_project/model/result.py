from crawl_taobao_goods_migrate.model.task import Task
from pyspider.core.model.mongo_base import *
from pyspider.helper.date import Date


class Result(ResultBase):
    def __init__(self):
        super(Result, self).__init__()

    def find_by_goods_id(self, goods_id):
        """
        从 goods image 库查找商品
        :param goods_id:
        :return:
        """
        return self.find_one({"taskid": Task.get_task_id_goods_image(goods_id)})

    def find_all_goods(self, shop_id=''):
        """
        查询 goods 库里的所有商品;
        有 shop_id 则查询该 shop_id 下的所有商品，否则就返回所有的商品;
        :param shop_id: 店铺ID
        :return:
        """
        builder = {
            'goods_id': {'$exists': 'true'},
        }
        if shop_id:
            builder['shop_id'] = shop_id
        return self.find(builder)

    def find_all_shop_id(self):
        """
        获取所有的店铺ID
        :return:
        """
        return self.find({
            'result.shop_id': {'$exists': 'true'},
            'result.shop_url': {'$exists': 'true'},
            'result.banner_imgs': {'$exists': 'true'},
        })

    def find_shop_by_id(self, shop_id):
        """
        从 shop details 库查找店铺详情
        :param shop_id:
        :return:
        """
        return self.find_one({"taskid": Task.get_task_id_shop_details(shop_id)})

    def update_shop_crawled_status(self, shop_id, status):
        """
        更改店铺的被抓取的状态
        :param shop_id:
        :param status:
        :return:
        """
        return self.update_many({'taskid': Task.get_task_id_shop_details(shop_id)},
                                {"$set": {"result.crawled": status}})

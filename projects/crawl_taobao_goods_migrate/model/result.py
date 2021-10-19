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

    def find_complete_goods(self, goods_id):
        """
        从 goods image 和 goods details 两个库中同时查找数据，返回更新时间较新的结果;
        如果能查到两条记录,说明有一个商品已经下架了
        :param goods_id:
        :return:
        """
        image_goods = self.find_one({"taskid": Task.get_task_id_goods_image(goods_id)})
        detail_goods = self.find_one({"taskid": Task.get_task_id_goods_detail(goods_id)})

        img_result = image_goods.get('result') if image_goods else "1970-01-01"
        detail_result = detail_goods.get('result') if detail_goods else "1970-01-01"

        img_date = img_result.get('update_time') if isinstance(img_result, dict) else "1970-01-01"
        detail_date = detail_result.get('update_time') if isinstance(detail_result, dict) else "1970-01-01"

        if img_date is None:
            img_date = "1970-01-01"
        if detail_date is None:
            detail_date = "1970-01-01"

        return detail_goods if Date(img_date) < Date(detail_date) else image_goods

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

    def find_all_shop_goods(self, shop_list: list):
        """
        获取所有的店铺商品ID
        :param shop_list: str list
        :return:
        """
        builder = {
            "goods_id": {"$exists": 'true'}
        }
        if shop_list:
            shop_list = [str(item) for item in shop_list]
            builder["shop_id"] = {"$in": shop_list}
        return self.find(builder)

    def find_filter_goods(self, shop_ids: list, update_time=0):
        """
        过滤查询商品数据
        :param shop_ids: int list
        :param update_time: 如果有更新时间，则获取小于更新时间的商品
        :return:
        """
        builder = {
            'result.goods_id': {'$exists': 'true'},
        }
        if shop_ids:
            shop_ids = [int(item) for item in shop_ids]
            builder['result.shop_id'] = {"$in": shop_ids}
        if update_time > 0:
            builder['updatetime'] = {"$gte": update_time}
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

    def insert_or_update_goods(self, doc):
        """
        写入或者更新天猫商品
        :param doc:
        :return:
        """
        goods_id = doc.get("goods_id", "")
        goods_name = doc.get("goods_name", "")
        shop_id = doc.get("shop_id", "")
        update_time = doc.get("update_time", 0)
        if goods_id:
            re = self.find_one({"goods_id": goods_id})
            if re:
                return self.update(
                    {'goods_id': goods_id},
                    {"$set": {"goods_id": goods_id, "goods_name": goods_name, "shop_id": shop_id,
                              "update_time": update_time}})
            else:
                return self.insert(doc)
        else:
            return self.insert(doc)

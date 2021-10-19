from pyspider.core.model.mongo_base import *


class Result(ResultBase):
    def __init__(self):
        super(Result, self).__init__()

    def find_comment_by_barcode(self, shop_type, barcode, page, page_size):
        """
        用货号获取已抓取的所有评论
        :param shop_type:
        :param barcode:
        :return:
        """
        transfer_dict = {
            1: '淘宝',
            2: '天猫',
            3: '京东',
        }
        query = {'result.id': barcode}
        if shop_type:
            query['result.shop_type'] = int(shop_type)
        comments = self.find(query).skip(page * page_size).limit(page_size)
        return_dict = []
        for c in comments:
            result = c.get('result')
            c_shop_type = result.get('shop_type')
            if 'result' in result:
                result.pop('result')
            result['shopType'] = transfer_dict.get(int(c_shop_type))
            if 'shop_type' in result:
                result.pop('shop_type')
            return_dict.append(result)
        return return_dict

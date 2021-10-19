from pyspider.core.model.es_base import *


class BarcodeES(Base):
    def __init__(self):
        super(BarcodeES, self).__init__()
        self.index = 'ai_service_goods_data'
        self.doc_type = 'goods'
        self.primary_keys = ['goodsCode']

    def find_barcode_by_goods_id(self, shop_type, goods_id):
        """
        通过 goods ID 返回 barcode
        :param shop_type: 店铺类型，淘宝，天猫，还是京东。。。
        :param goods_id: 商品 ID
        :return:
        """
        if shop_type == 1:
            query_type_name = 'taobaoGoodsId'
        elif shop_type == 2:
            query_type_name = 'tmallGoodsId'
        elif shop_type == 3:
            query_type_name = 'jdGoodsId'
        else:
            return ''
        query = {
            "query": {
                "term": {
                    query_type_name: {
                        "value": goods_id,
                    }
                }
            }
        }
        result = self.search(query)
        result = result.get('hits').get('hits')
        return result

    def get_all_jingdong_goods(self):
        """
        获取京东渠道的所有商品
        :return:
        """
        query = {
            "query": {
                "bool": {
                    "filter": {
                        "exists": {
                            "field": "jdGoodsId"
                        }
                    }
                }
            },
            "size": 5000
        }
        results = self.search(query)
        return_list = []
        for result in results.get('hits').get('hits'):
            barcode = result.get('_source').get('goodsCode')
            goods_id = result.get('_source').get('jdSkuId')
            if goods_id:
                goods_id = goods_id[0]
            return_list.append((goods_id, barcode))
        return return_list

    def get_barcode_goods_id_relationship(self, barcode, page=0, page_size=20):
        """
        根据货号获取货号和商品ID的对应关系
        :param barcode:
        :param page:
        :param page_size:
        :return:
        """
        query = {
            "from": page * page_size,
            "size": page_size,
            "sort": [
                {
                    "createTime": {
                        "order": "asc"
                    }
                }
            ]
        }
        if barcode:
            query['query'] = {"term": {"goodsCode": {"value": barcode}}}
        results = self.search(query)
        return_list = []
        for result in results.get('hits').get('hits'):
            goods_id_list = []
            barcode = result.get('_source').get('goodsCode')
            jd_goodsId = result.get('_source').get('jdSkuId')
            if jd_goodsId:
                jd_goodsId = jd_goodsId[0]
            tmall_goodsId = result.get('_source').get('tmallGoodsId')
            taobao_goodsId = result.get('_source').get('taobaoGoodsId')
            if jd_goodsId:
                goods_id_list.append({
                    'goods_id': jd_goodsId,
                    'shop_type': 3,
                })
            if tmall_goodsId:
                goods_id_list.append({
                    'goods_id': tmall_goodsId,
                    'shop_type': 2,
                })
            if taobao_goodsId:
                goods_id_list.append({
                    'goods_id': taobao_goodsId,
                    'shop_type': 1,
                })
            return_list.append({
                'id': barcode,
                'goods_id_list': goods_id_list,
            })
        return return_list

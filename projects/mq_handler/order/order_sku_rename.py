import traceback
from copy import deepcopy

from hupun_operator.page.order_sku_rename.sku_rename import OrSkuRename
from hupun_operator.page.order_sku_rename.sku_rename_query import OrSkuReQuery
from hupun_operator.page.order_split.order_number_query import OrderNumQuery
from hupun_operator.page.order_split.split_order_goods import SplitOrderGoods
from mq_handler.base import Base
from pyspider.helper.crawler_utils import CrawlerHelper
from pyspider.helper.utils import generator_list


class OrderSkuRename(Base):
    """
    万里牛 修改订单下的商品sku
    """
    SKU_SUFFIX = '-YS'

    def execute(self):
        print('接收万里牛修改订单下的商品sku名称的内容')
        self.print_basic_info()

        # 写入数据
        try:
            if not isinstance(self._data.get('data'), list):
                raise Exception('传入的数据格式不对')
            for data_list in generator_list(self._data.get('data'), 400):
                for data in data_list:
                    try:
                        self.entry(data)
                    except Exception as e:
                        err_msg = '修改订单下的商品sku失败,err_msg:{};'.format(e)
                        print(err_msg)
                        print(traceback.format_exc())

        except Exception as e:
            err_msg = '修改订单下的商品sku失败,err:{};'.format(e)
            print(err_msg)
            print(traceback.format_exc())

    def entry(self, data):
        """
        执行操作的入口
        :param data: 每一条需要重命名sku的订单
        :return:
        """
        print('开始根据订单号执行商品重命名操作')
        tp_tid = data['tp_tid']

        # 获取订单的数据, 这个地方的订单数据跟拆单脚本的订单数据获取方式相同
        order_obj = OrderNumQuery(tp_tid).set_cookie_position(1)
        order_status, order_result = CrawlerHelper.get_sync_result(order_obj)
        if order_status != 0:
            raise Exception(order_result)
        if not isinstance(order_result, list) or not order_result:
            raise Exception('在万里牛没有获取到订单:{}的详情'.format(tp_tid))

        for order in order_result:
            try:
                trade_uid = order['salercpt_uid']
                storage_name = order['storage_name']
                storage_uid = order['storage_uid']
                history = 'true' if order['history'] else 'false'

                # 获取订单的数据, 这个地方的订单商品数据跟拆单脚本的订单商品数据获取方式相同
                goods_obj = SplitOrderGoods(trade_uid, storage_uid, history).set_cookie_position(1)
                goods_st, goods_re = CrawlerHelper.get_sync_result(goods_obj)
                if goods_st != 0:
                    raise Exception(goods_re)
                if not isinstance(goods_re, list) or not goods_re:
                    raise Exception('在万里牛没有获取到被改商品名订单:{}的商品详情'.format(tp_tid))

                # 查询所有需要重命名的商品,一次发送更改的请求
                for goods in goods_re:
                    sku_id = goods['spec_code']
                    if sku_id.endswith(self.SKU_SUFFIX):
                        origin_goods = deepcopy(goods)
                        goods['spec_code'] = sku_id.replace(self.SKU_SUFFIX, '')

                        # 查询需要重命名商品的重命名后的商品数据
                        sku_rename_obj = OrSkuReQuery(goods['spec_code']).set_cookie_position(1)
                        sku_rename_st, sku_rename_re = CrawlerHelper.get_sync_result(sku_rename_obj)
                        if sku_rename_st != 0:
                            raise Exception(sku_rename_re)
                        if not isinstance(sku_rename_re, list) or not sku_rename_re:
                            raise Exception('未查询到被改名商品:{}的信息')
                        rename_goods = {}
                        for index, _sku in enumerate(sku_rename_re):
                            if _sku['specCode'] == goods['spec_code']:
                                rename_goods = deepcopy(goods)
                                rename_goods['specValue'] = _sku['specValue']
                                rename_goods['sys_sku_id'] = _sku['specUid']
                                rename_goods['spec1_value'] = _sku['specValue1']
                                rename_goods['spec_code'] = _sku['specCode']
                                rename_goods['specName'] = _sku['specValue']
                                rename_goods['$dataType'] = 'v:sale.approve$Order'
                                rename_goods['$entityId'] = "0"
                                break
                            if index == len(sku_rename_re) - 1:
                                raise Exception('未查询到被改名商品:{}在二次查询里的信息')

                        # 组装修改商品sku的参数
                        self.assemble_sku_args(order, goods_re, rename_goods, origin_goods, tp_tid)

            except Exception as e:
                err_msg = '修改订单下的商品sku失败,tp_tid:{},err:{};'.format(tp_tid, e)
                print(err_msg)
                print(traceback.format_exc())

    def assemble_sku_args(self, tp_tid_data, origin_sku_data, rename_goods, old_rename_goods, tp_tid):
        """
        执行订单商品的改名操作
        :param tp_tid_data: 订单信息
        :param origin_sku_data: 订单对应的原始商品信息
        :param rename_goods: 需要改名的商品信息
        :param old_rename_goods: 老的需要改名的商品信息
        :param tp_tid: 订单号
        :return:
        """
        tp_data = deepcopy(tp_tid_data)
        sku_data = deepcopy(origin_sku_data)
        rename_goods = deepcopy(rename_goods)
        old_rename_goods = deepcopy(old_rename_goods)

        # 构造"alias": "order" 部分的商品数据
        rename_goods['sn'] = {
            "$isWrapper": True,
            "$dataType": "v:sale.approve$[dtSerialNumber]",
            "data": []
        }
        rename_goods['batch'] = {
            "$isWrapper": True,
            "$dataType": "v:sale.approve$[dtBatch]",
            "data": []
        }
        rename_goods['$dataType'] = "v:sale.approve$Order"
        rename_goods['$state'] = "2"
        rename_goods['$entityId'] = "0"
        rename_goods['$oldData'] = old_rename_goods

        # 订单对应的原始数据
        order_inner_data = []
        for sku in sku_data:
            inner_sku = deepcopy(sku)
            # inner_sku['unpackCount'] = 1
            inner_sku['sn'] = {
                "$isWrapper": True,
                "$dataType": "v:sale.approve$[dtSerialNumber]",
                "data": []
            }
            inner_sku['batch'] = {
                "$isWrapper": True,
                "$dataType": "v:sale.approve$[dtBatch]",
                "data": []
            }
            inner_sku['$dataType'] = "v:sale.approve$Order"
            inner_sku['$entityId'] = "0"
            order_inner_data.append(inner_sku)

        # 构造"alias": "trade" 部分的商品数据(订单数据+对应的原始商品数据)
        first_tier_data = deepcopy(tp_data)
        first_tier_data['order'] = {
            "$isWrapper": True,
            "$dataType": "v:sale.approve$[Order]",
            "data": order_inner_data
        }
        first_tier_data['$dataType'] = "Trade"
        first_tier_data['$entityId'] = "0"

        osr_obj = OrSkuRename(first_tier_data, rename_goods) \
            .set_cookie_position(1)
        osr_status, osr_result = CrawlerHelper.get_sync_result(osr_obj)
        if osr_status != 0 or 'err_details' in osr_result:
            err_msg = '商品sku更改失败,订单号:{},失败原因:{}'.format(tp_tid, osr_result)
            print('err_msg', err_msg)
            raise Exception(err_msg)
        if not osr_result.get('entityStates'):
            err_msg = '商品sku更改失败,订单号:{},失败原因:操作拆单返回的结果不正确:{}'.format(tp_tid, osr_result.get('entityStates'))
            print('err_msg', err_msg)
            raise Exception(err_msg)
        print('订单:{}的商品sku更改成功'.format(tp_tid))

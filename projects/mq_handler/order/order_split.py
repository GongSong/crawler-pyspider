import traceback
from copy import deepcopy

from hupun_operator.page.order_split.order_number_query import OrderNumQuery
from hupun_operator.page.order_split.order_remark import OrderRemark
from hupun_operator.page.order_split.order_sku_query_exists import OrderSkuQueryExists
from hupun_operator.page.order_split.order_split_operate import OrderSplitOp
from hupun_operator.page.order_split.split_order_goods import SplitOrderGoods
from mq_handler.base import Base
from pyspider.helper.crawler_utils import CrawlerHelper
from pyspider.helper.input_data import InputData


class OrderSplit(Base):
    """
    万里牛包含【预售SKU】的订单拆单
    """

    def execute(self):
        print('接收万里牛包含【预售SKU】的订单拆单的内容')
        self.print_basic_info()

        # 写入数据
        try:
            if not isinstance(self._data.get('data'), list):
                raise Exception('传入的数据格式不对')
            for data in self._data.get('data'):
                try:
                    # split_type 为拆分类别，1为根据订单号拆分，2为根据sku商品拆分
                    split_type = InputData(data).get_int('split_type')
                    if split_type == 1:
                        # 根据订单号拆分
                        self.entry(data)
                    elif split_type == 2:
                        # 根据sku拆分
                        self.sku_split_entry(data)
                    else:
                        err_msg = '传入的订单类型不对:{}'.format(split_type)
                        raise Exception(err_msg)
                except Exception as e:
                    err_msg = '预售sku的订单拆单err:{};'.format(e)
                    print(err_msg)
                    print(traceback.format_exc())

        except Exception as e:
            err_msg = '预售sku的订单拆单err:{};'.format(e)
            print(err_msg)
            print(traceback.format_exc())

    def entry(self, data):
        """
        执行操作的入口
        :param data: 每一条需要拆分的订单
        :return:
        """
        print('开始根据订单号执行拆单操作')
        tp_tid = data['tp_tid']
        skus = data['skus']
        remark = data['remark']
        if not isinstance(skus, list) or not skus:
            raise Exception('传入的sku: {} 不符合规范，不能被正确处理'.format(skus))

        # 获取订单的数据
        order_obj = OrderNumQuery(tp_tid).set_cookie_position(1)
        order_status, order_result = CrawlerHelper.get_sync_result(order_obj)
        if order_status != 0:
            raise Exception(order_result)
        if not isinstance(order_result, list) or not order_result:
            raise Exception('在万里牛没有获取到订单:{}的详情'.format(tp_tid))

        for order in order_result:
            goods_sum = int(order['goods_count'])
            trade_uid = order['salercpt_uid']
            storage_name = order['storage_name']
            storage_uid = order['storage_uid']
            history = 'true' if order['history'] else 'false'
            # 获取订单的数据
            goods_obj = SplitOrderGoods(trade_uid, storage_uid, history).set_cookie_position(1)
            goods_st, goods_re = CrawlerHelper.get_sync_result(goods_obj)
            if goods_st != 0:
                raise Exception(goods_re)
            if not isinstance(goods_re, list) or not goods_re:
                raise Exception('在万里牛没有获取到被拆分订单:{}的商品详情'.format(tp_tid))

            # 开始拆单逻辑
            if goods_sum > 1 and goods_sum != len(skus):
                # 商品总数大于1，可以拆单
                print('商品总数大于1，可以拆单')

                # 查询所有需要拆分的商品是否存在,保存好需要拆分和不拆分的商品
                split_goods = []
                not_split_goods = []
                for sku in skus:
                    for index, goods in enumerate(goods_re):
                        sku_id = goods['spec_code']
                        if sku_id == sku:
                            print('查询到了sku:{}'.format(sku_id))
                            split_goods.append(goods)
                            break
                        elif index == len(goods_re):
                            err_msg = '订单:{}不包含商品:{}'.format(tp_tid, sku_id)
                            print(err_msg)
                            raise Exception(err_msg)
                for g in goods_re:
                    if g['spec_code'] not in skus:
                        not_split_goods.append(g)

                # 开始拆分订单
                print('需要拆分的商品正常,开始拆分订单')
                self.split_order(order, split_goods, not_split_goods, storage_name, storage_uid, tp_tid, remark)
            else:
                # 商品总数不大于1,或者拆单商品总数与订单内的商品总数相同,不拆单,需要备注
                print('商品总数不大于1,或者拆单商品总数与订单内的商品总数相同,不拆单,需要备注')

            print('开始给商品追加备注')
            # 组合订单备注的信息
            sku_data = []
            for _goods in goods_re:
                copy_sku = deepcopy(_goods)
                copy_sku['$dataType'] = 'v:sale.approve$Order'
                copy_sku['$state'] = 2
                copy_sku['$entityId'] = "0"
                sku_data.append(copy_sku)

            order_remark_data = deepcopy(order)
            order_remark_data['isChooseCustom'] = True if order.get('isChooseCustom') else False
            order_remark_data['remark'] = remark
            order_remark_data['$dataType'] = 'Trade'
            order_remark_data['$state'] = 2
            order_remark_data['$entityId'] = '0'
            order_remark_data['order'] = {
                "$isWrapper": True,
                "$dataType": "v:sale.approve$[Order]",
                "data": sku_data
            }
            old_remark = '' if not order['remark'] else order['remark']
            new_remark = old_remark + ';' + remark

            remark_obj = OrderRemark(order_remark_data, old_remark, new_remark).set_cookie_position(1)
            remark_st, remark_re = CrawlerHelper.get_sync_result(remark_obj)
            if remark_st != 0:
                raise Exception(remark_re)
            if not isinstance(remark_re.get('entityStates'), dict) or not remark_re.get('entityStates'):
                raise Exception('在万里牛更改订单:{}备注失败'.format(tp_tid))
            print('在万里牛更改订单:{}备注成功'.format(tp_tid))

    def split_order(self, tp_tid_data, split_goods, not_split_goods, storage_name, storage_uid, tp_tid,
                    remark='spider_split'):
        """
        执行拆分订单的操作
        :param tp_tid_data: 订单信息
        :param split_goods: 需要拆分的商品信息
        :param not_split_goods: 另一批不需要拆分的商品信息
        :param storage_name: 仓库名
        :param storage_uid: 仓库uid
        :param tp_tid: 订单号
        :param remark: 备注
        :return:
        """
        tp_data = deepcopy(tp_tid_data)
        split_sku_list = deepcopy(split_goods)
        not_split_sku_list = deepcopy(not_split_goods)

        # 被拆分的目标订单商品
        order_goods = []
        for sku in not_split_sku_list:
            goods = deepcopy(sku)
            old_data = deepcopy(sku)
            goods['sn'] = {
                "$isWrapper": True,
                "$dataType": "v:sale.approve$[dtSerialNumber]",
                "data": []
            }
            goods['batch'] = {
                "$isWrapper": True,
                "$dataType": "v:sale.approve$[dtBatch]",
                "data": []
            }
            goods['$dataType'] = "v:sale.approve$Order"
            goods['$state'] = "2"
            goods['$entityId'] = "0"
            goods['$oldData'] = old_data
            order_goods.append(goods)

        # 未被拆单的数据
        first_tier_data = deepcopy(tp_data)
        old_first_tier_data = deepcopy(tp_data)
        first_tier_data['order'] = {
            "$isWrapper": True,
            "$dataType": "v:sale.approve$[Order]",
            "data": order_goods
        }
        first_tier_data['$dataType'] = "Trade"
        first_tier_data['$entityId'] = "0"
        first_tier_data['$state'] = "2"
        first_tier_data['$oldData'] = old_first_tier_data

        # 被拆单的数据
        second_tier_data = []
        split_goods_list = deepcopy(split_sku_list)
        for s_goods in split_goods_list:
            inner_sku = deepcopy(s_goods)
            inner_sku['storageName'] = storage_name
            inner_sku['storageUid'] = storage_uid
            inner_sku['unpackCount'] = 1
            inner_sku['$dataType'] = "v:sale.approve$Order"
            inner_sku['$state'] = 1
            inner_sku['$entityId'] = "0"
            second_tier_data.append(inner_sku)

        op_obj = OrderSplitOp(first_tier_data, second_tier_data, storage_uid, storage_name, remark=remark) \
            .set_cookie_position(1)
        op_status, op_result = CrawlerHelper.get_sync_result(op_obj)
        if op_status != 0 or 'err_details' in op_result:
            err_msg = '拆单失败,订单号:{},失败原因:{}'.format(tp_tid, op_result)
            print('err_msg', err_msg)
            raise Exception(op_result)
        if not op_result.get('entityStates'):
            err_msg = '拆单失败,订单号:{},失败原因:操作拆单返回的结果不正确:{}'.format(tp_tid, op_result.get('entityStates'))
            print('err_msg', err_msg)
            raise Exception(err_msg)
        print('订单:{}拆单成功'.format(tp_tid))

    def sku_split_entry(self, data):
        """
        根据sku拆分
        :param data: 每一条需要拆分的订单
        :return:
        """
        print('开始根据sku拆分订单')
        skus = data['skus']
        remark = data['remark']
        if not isinstance(skus, list) or not skus:
            raise Exception('传入的sku: {} 不符合规范，不能被正确处理'.format(skus))
        for sku in skus:
            try:
                sku_query_obj = OrderSkuQueryExists(sku).set_cookie_position(1)
                sku_query_st, sku_query_re = CrawlerHelper.get_sync_result(sku_query_obj)
            except Exception as e:
                print('拆分商品:{}失败,error:{}'.format(sku, e))

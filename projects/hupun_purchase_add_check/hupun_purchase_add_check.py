import fire
from alarm.page.ding_talk import DingTalk
from cookie.config import ROBOT_TOKEN
from hupun.model.es.purchase_order import PurchaseOrder
from hupun.model.es.purchase_order_add_msg import PurOrderAddMsg
from hupun.model.es.purchase_order_goods import PurchaseOrderGoods
from pyspider.core.model.storage import default_storage_redis
from pyspider.helper.es_query_builder import EsQueryBuilder
from pyspider.helper.date import Date
from pyspider.helper.logging import processor_logger


class Cron:
    def purchase_add_check(self, days=1):
        '''
        检查采购订单是否正确同步
        :param days:
        :return:
        '''
        CHEDCKED_ORDER_DOMIN = 'checked_add_order'
        print('开始检查采购订单是否正确同步')
        try:
            ding_msg = ''
            save_order_list = PurOrderAddMsg().scroll(
                    EsQueryBuilder()
                    .range('create_time', Date().now().plus_days(-days)
                    .format_es_old_utc(), None),
                        page_size=100
                    )

            save_bill_code_dict = {}
            for _list in save_order_list:
                for _item in _list:
                    # 过滤掉测试的订单
                    if _item['storage_name'] != '研发测试仓':
                        save_bill_code_dict.setdefault(_item['bill_code'], _item)
            save_bill_code_list = list(save_bill_code_dict.keys())

            search_order_list = PurchaseOrder().scroll(
                        EsQueryBuilder()
                        .range('bill_date', Date().now().plus_days(-days).format_es_old_utc(), None)
                        .term('billCreater', '系统管理员')
                        .source(['bill_code', 'bill_date', 'supplier_name',
                                'storage_name', 'status', 'billCreater', 'bill_uid', 'remark']),
                        page_size=100
                    )

            search_bill_code_dict = {}
            for _list in search_order_list:
                for _item in _list:
                    # 过滤掉测试的订单
                    if _item['storage_name'] != '研发测试仓' and '爬虫自己在执行过程中的关闭' not in _item['remark']:
                        search_bill_code_dict.setdefault(_item['bill_code'], _item)
            search_bill_code_list = list(search_bill_code_dict.keys())

            checked_order_list = self.get_domin_list_redis(CHEDCKED_ORDER_DOMIN)
            to_check_order_list = list(set(search_bill_code_list).union(set(save_bill_code_list)))
            # 对比保存的订单和从erp爬取的订单的不同
            save_over_order_list = list(set(save_bill_code_list).difference(set(search_bill_code_list)))
            search_over_order_list = list(set(search_bill_code_list).difference(set(save_bill_code_list)))
            # 将对比后的订单列表减去已检测过的订单
            filted_save_over_order_list = list(set(save_over_order_list).difference(set(checked_order_list)))
            filted_search_over_order_list = list(set(search_over_order_list).difference(set(checked_order_list)))

            if filted_save_over_order_list:
                warning_msg = '检测到erp少生成以下订单：{}，请到线上及时检查。'.format('，'.join(filted_save_over_order_list))
                ding_msg += warning_msg
            if filted_search_over_order_list:
                warning_msg = '检测到erp多生成以下订单：{}，请到线上及时检查。'.format('，'.join(filted_search_over_order_list))
                ding_msg += warning_msg
            same_order_list = list(set(save_bill_code_list).intersection(set(search_bill_code_list)))
            for _bill_code in same_order_list:
                _save_order_dict = save_bill_code_dict.get(_bill_code)
                _search_order_dict = search_bill_code_dict.get(_bill_code)
                # 如果有status不是【1，2，3，4】中的中间状态则报错不在对比
                # 其中status=1 未到货 status=2 部分到货 status=3 已完成 status=4 已关闭
                if _search_order_dict['status'] not in [1, 2, 3, 4]:
                    warning_msg = '查询到采购订单:{}状态未同步完整，请到线上及时检查。'.format(_bill_code)
                    ding_msg += warning_msg
                    continue
                if _save_order_dict['storage_name'] != _search_order_dict['storage_name']:
                    warning_msg = '查询到采购订单:{}信息未正确同步，请到线上及时检查。'.format(_bill_code)
                    ding_msg += warning_msg
                    continue
                _search_goods_dict = EsQueryBuilder() \
                        .term('bill_uid', _search_order_dict['bill_uid']) \
                        .search(PurchaseOrderGoods(), 1, 200) \
                        .get_list()
                _save_goods_list = _save_order_dict['goods']
                # 如订单信息无问题，则继续检查该订单下的所有商品信息
                warning_msg = self.compare_add_goods_list(_save_goods_list, _search_goods_dict, _bill_code)
                ding_msg += warning_msg
            self.save_list_redis(to_check_order_list, CHEDCKED_ORDER_DOMIN, ex=86400)
            if ding_msg:
                print(ding_msg)
                title = '同步采购订单的校验程序警告'
                DingTalk(ROBOT_TOKEN, title, ding_msg).enqueue()
            else:
                print('检测完成，上次检测后无新增任何未正确同步的订单。')
        except Exception as e:
            print('检查采购订单是否正确同步失败: {}，请重新检测。')
            processor_logger.warning('检查采购订单是否正确同步失败: {}，请重新检测。'.format(e))

    def compare_add_goods_list(self, save_goods_list, search_goods_list, bill_code):
        ding_msg = ''
        save_good_compare_dict = {}
        for _save_good in save_goods_list:
            save_good_compare_dict.setdefault(_save_good['sku_barcode'], _save_good)
        save_good_compare_list = list(save_good_compare_dict.keys())
        search_good_compare_dict = {}
        for _search_good in search_goods_list:
            search_good_compare_dict.setdefault(_search_good['spec_code'], _search_good)
        search_good_compare_list = list(search_good_compare_dict.keys())
        save_over_good_list = list(set(save_good_compare_list).difference(set(search_good_compare_list)))
        search_over_good_list = list(set(search_good_compare_list).difference(set(save_good_compare_list)))

        if save_over_good_list:
            warning_msg = 'erp的订单：{0}少生成以下商品{1}，请到线上及时检查。'.format(bill_code, '，'.join(save_over_good_list))
            ding_msg += warning_msg
        if search_over_good_list:
            warning_msg = 'erp的订单：{0}多生成以下商品{1}，请到线上及时检查。'.format(bill_code, '，'.join(search_over_good_list))
            ding_msg += warning_msg

        same_good_list = list(set(save_good_compare_list).intersection(set(search_good_compare_list)))
        for sku_barcode in same_good_list:
            _save_good_dict = save_good_compare_dict.get(sku_barcode)
            _search_order_dict = search_good_compare_dict.get(sku_barcode)
            if _save_good_dict['purchase_count'] != _search_order_dict['pchs_size'] or \
                    _save_good_dict['price'] != _search_order_dict['pchs_base_price']:
                warning_msg = '查询到采购订单:{0}的商品{1}未正确同步，请到线上及时检查。'.format(bill_code, sku_barcode)
                ding_msg += warning_msg
        return ding_msg

    def get_domin_list_redis(self, domin):
        '''
        根据key的域名获取，该域名下的所有key的值。bill_code的domin为'checked_add_order'
        '''
        bill_code_redis_list = []
        for key in default_storage_redis.keys('%s:*' % domin):
            bill_code_redis_list.append(default_storage_redis.get(key))
        return bill_code_redis_list

    def save_list_redis(self, list, domin, ex=None):
        '''
        将list内的数据存入某域名下的redis中
        '''
        for key in list:
            final_key = '{}:{}'.format(domin, key)
            default_storage_redis.set(final_key, key, ex=ex)


if __name__ == '__main__':
    fire.Fire(Cron)

from pyspider.core.model.mysql_base import *

"""
保存商品流量来源的数据
"""


class GoodsFlowSources(Model):
    main_id = CharField(primary_key=True, max_length=100, verbose_name='goods_id + date_str + sources_name')
    goods_id = CharField(max_length=50, verbose_name='天猫商品ID')
    sources_name = CharField(verbose_name='来源名称')
    visitor_num = IntegerField(default=0, verbose_name='访客数')
    page_views = IntegerField(default=0, verbose_name='浏览量')
    pay_amount = FloatField(default=0.0, verbose_name='支付金额')
    percent_visitor = FloatField(default=0.0, verbose_name='浏览量占比')
    store_jump_num = IntegerField(default=0, verbose_name='店内跳转人数')
    store_jump_out_num = IntegerField(default=0, verbose_name='跳出本店人数')
    collect_num = IntegerField(default=0, verbose_name='收藏人数')
    add_pur_num = IntegerField(default=0, verbose_name='加购人数')
    buyer_num = IntegerField(default=0, verbose_name='下单买家数')
    order_conv_rate = FloatField(default=0.0, verbose_name='下单转化率')
    payment_num = IntegerField(default=0, verbose_name='支付件数')
    buyer_pay_num = IntegerField(default=0, verbose_name='支付买家数')
    payment_conv_rate = FloatField(default=0.0, verbose_name='支付转化率')
    direct_payment_buyer_num = IntegerField(default=0, verbose_name='直接支付买家数')
    collect_paid_buyer_num = IntegerField(default=0, verbose_name='收藏商品-支付买家数')
    fans_paid_buyer_num = IntegerField(default=0, verbose_name='粉丝支付买家数')
    add_pur_paid_buyer_num = IntegerField(default=0, verbose_name='加购商品-支付买家数')
    date_str = CharField(max_length=20, verbose_name='数据被生成时的日期, eg: 2019-10-29')
    update_time = DateTimeField(default=None, verbose_name='数据写入日期')

    class Meta:
        database = db
        db_table = 'spider_goods_flow_sources'
        indexes = (
            (('goods_id', 'date_str', 'sources_name'), True),
        )

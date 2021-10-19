from pyspider.core.model.mysql_base import *

"""
万里牛库存sku数据的保存模块
"""


class WholeInoutOrder(Model):
    id = IntegerField(primary_key=True)
    bill_id = CharField(verbose_name='唯一入库单ID')
    bill_code = CharField(verbose_name='出入库单号')
    bill_time = DateTimeField(verbose_name='出入库时间')
    bill_date = DateField(verbose_name='业务日期')
    bill_type = CharField(verbose_name='出入库类型')
    storage_id = CharField(verbose_name='仓库ID')
    storage_name = CharField(verbose_name='仓库名字')
    spu = CharField(verbose_name='商品编码')
    sku = CharField(verbose_name='规格编码')
    goods_name = CharField(verbose_name='商品名称')
    category_name = CharField(verbose_name='品类名')
    goods_color = CharField(verbose_name='颜色')
    goods_size = CharField(verbose_name='尺码')
    remark = CharField(verbose_name='备注')
    in_or_out = IntegerField(verbose_name='出入库数量')
    quantity = IntegerField(verbose_name='库存结余')
    cost_price = DecimalField(verbose_name='不含税成本单价')
    cost_total = DecimalField(verbose_name='不含税成本总价')
    cost_tax_rate = DecimalField(verbose_name='成本税率')
    cost_price_after_tax = DecimalField(verbose_name='成本单价')
    cost_total_after_tax = DecimalField(verbose_name='成本总价')
    sale_price = DecimalField(verbose_name='不含税销售单价')
    sale_total = DecimalField(verbose_name='不含税销售金额')
    sale_tax_rate = DecimalField(verbose_name='销售税率')
    sale_price_after_tax = DecimalField(verbose_name='销售单价')
    sale_total_after_tax = DecimalField(verbose_name='销售金额')
    shop_name = CharField(verbose_name='店铺')
    tp_tid = CharField(verbose_name='线上订单号')
    trade_no = CharField(verbose_name='系统订单号')
    custom_nick = CharField(verbose_name='买家ID')
    custom_name = CharField(verbose_name='客户')
    cellphone = CharField(verbose_name='手机号码')
    address = CharField(verbose_name='地址')
    oper_nick = CharField(verbose_name='经手人')
    express = CharField(verbose_name='快递公司')
    express_uid = CharField(verbose_name='快递单号')
    pay_way = CharField(verbose_name='付款方式')
    created_at = DateTimeField(verbose_name='创建时间')
    updated_at = DateTimeField(verbose_name='最后一次更新时间')

    class Meta:
        database = xs_report_db
        db_table = 'online_stock_detail'

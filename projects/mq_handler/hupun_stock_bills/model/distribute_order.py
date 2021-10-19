from pyspider.core.model.mysql_base import *

"""
万里牛库存sku数据的保存模块
"""


class DistributeOrder(Model):
    uid = IntegerField(verbose_name='自增主键')
    distribution_id = CharField(max_length=50, verbose_name='配货单号')
    submitter = IntegerField(verbose_name='提交人')
    expect_delivery_time = IntegerField(verbose_name='期望送达日期')
    deliver_warehouse_id = IntegerField(verbose_name='发货仓/门店')
    receipt_warehouse_id = IntegerField(verbose_name='收货仓/门店')
    type = IntegerField(verbose_name='配货类型')
    remark = CharField(max_length=50, verbose_name='备注')
    status = IntegerField(verbose_name='配货单状态')
    submit_time = IntegerField(verbose_name='提交时间 - 即创建时间')
    update_time = IntegerField(verbose_name='更新时间')
    erp_invoice_order = CharField(max_length=50, verbose_name='erp发货单id')
    erp_receipt_order = CharField(max_length=50, verbose_name='erp收货单id')
    erp_sync_status = CharField(max_length=50, verbose_name='erp同步状态')


    class Meta:
        database = erp_db
        db_table = 'distribute_order'

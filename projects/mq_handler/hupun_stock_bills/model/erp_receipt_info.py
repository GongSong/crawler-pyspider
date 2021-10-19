from pyspider.core.model.mysql_base import *

"""
万里牛收货单信息表数据的保存模块
"""


class ErpReceiptInfo(Model):
    id = IntegerField(verbose_name='主键')
    receipt_id = CharField(max_length=50, verbose_name='收货单id')
    erp_outbound = CharField(max_length=50, verbose_name='万里牛出库单')
    outbound = CharField(max_length=50, verbose_name='出库单')
    create_time = IntegerField(verbose_name='更新时间')


    class Meta:
        database = erp_shop_db
        db_table = 'erp_receipt_info'

from pyspider.core.model.mysql_base import *

"""
万里牛订单数据的保存模块;
暂时不使用mysql保存订单数据，因为这个订单数据的字段太多，而且还有二级类目;
"""


class OrderSQL(Model):
    goods_code = CharField(max_length=50, verbose_name='商品编码')
    lock_size = DoubleField(default=0, verbose_name='锁定库存')
    quantity = DoubleField(default=0, verbose_name='数量')
    sku_code = CharField(max_length=50, default='', verbose_name='规格编码')
    underway = DoubleField(default='', verbose_name='在途库存')
    update_time = TimestampField(default=None, verbose_name='爬虫更新日期')
    storage_code = CharField(max_length=50, default='', verbose_name='仓库编码')

    class Meta:
        database = db
        db_table = 'spider_order'
        # 设置索引
        indexes = (
            (('sku_code', 'storage_code'), True),
        )

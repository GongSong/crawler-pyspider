from pyspider.core.model.es_base import *


class EsVipProductDetail(Base):
    GOODS_ID = EsField("merchandiseNo", name="商品ID", es_type="string")
    NAME = EsField("name", name="商品名称", es_type="string")
    IMAGE_URL = EsField("imageUrl", name="图片URL", es_type="string")
    SPU_BARCODE = EsField("osn", name="spu号", es_type="string")
    SYNC_TIME = EsField("sync_time", name="同步时间", es_type="string")
    SHELF_STATUS = EsField("onSale", name="上下架状态", es_type="bool")
    INVENTORY = EsField("bindLeavingNum", name="库存数量", es_type="sum")

    def __init__(self):
        super(EsVipProductDetail, self).__init__()
        self.cli = es_cli
        self.index = 'vip_product_detail'
        self.test_index = 'vip_product_detail_test'
        self.doc_type = 'data'
        self.primary_keys = [self.GOODS_ID]

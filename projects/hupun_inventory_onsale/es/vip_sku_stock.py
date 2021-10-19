from pyspider.core.model.es_base import *


class EsVipSkuStock(Base):
    SKUBARCODE = EsField("skuBarcode", name="唯品会商品sku", es_type="string")
    SPU_BARCODE = EsField("spuBarcode", name="唯品会商品spu", es_type="string")
    SYNC_TIME = EsField("syncTime", name="同步时间", es_type="string")
    INVENTORY = EsField("skuStock", name="库存数量", es_type="sum")

    def __init__(self):
        super(EsVipSkuStock, self).__init__()
        self.cli = es_cli
        self.index = 'vip_sku_stock'
        self.test_index = 'vip_sku_stock_test'
        self.doc_type = 'data'
        self.primary_keys = [self.SKUBARCODE]

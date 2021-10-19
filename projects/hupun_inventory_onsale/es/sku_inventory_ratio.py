from pyspider.core.model.es_base import *


class EsSkuInventoryRatio(Base):
    ''' 小红书和app的sku_barcode用渠道id，其余用内部id '''
    SKU_BARCODE = EsField("skuBarcode", name="SKU号", es_type="string")
    CHANNEL = EsField("channel", name="渠道", es_type="string")  # 简称，天猫等
    STORAGE = EsField("storage", name="仓库", es_type="string")  # 总仓等
    QUANTITY_TYPE = EsField("quantityType", name="库存种类", es_type="string") # 1，2
    UPLOAD_RATIO = EsField("uploadRatio", name="库存比例", es_type="string")
    VIRTUAL_INVENTORY = EsField("virtualInventory", name="虚拟库存", es_type="string")
    SPU_BARCODE = EsField("spuBarcode", name="SPU号", es_type="string")
    SYNC_TIME = EsField("syncTime", name="同步时间", es_type="date")
    SYNC_STATUS = EsField("syncStatus", name="同步状态", es_type="string")
    FAIL_REASON = EsField("failReason", name="失败原因", es_type="string")

    def __init__(self):
        super(EsSkuInventoryRatio, self).__init__()
        self.cli = es_cli
        self.index = 'sku_inventory_ratio'
        self.test_index = 'sku_inventory_ratio_test'
        self.doc_type = 'data'
        self.primary_keys = [self.SKU_BARCODE, self.CHANNEL, self.STORAGE]

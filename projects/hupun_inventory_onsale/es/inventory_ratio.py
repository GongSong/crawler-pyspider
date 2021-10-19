from pyspider.core.model.es_base import *


class EsInventoryRatio(Base):
    ''' 小红书和app的sku_barcode用渠道id，其余用内部id '''
    SKU_BARCODE = EsField("fakeSku", name="虚构SKU号", es_type="string")  # 唯品会为真实sku，其余渠道sku是与spu相同的虚构sku
    SPU_BARCODE = EsField("spuBarcode", name="SPU号", es_type="string")  # 内部id
    CHANNEL_PRODUCT_ID = EsField("channelProductId", name="渠道商品id", es_type="string")  # 渠道id
    CHANNEL = EsField("channel", name="渠道", es_type="string")
    NAME = EsField("name", name="小红书渠道商品名称", es_type="string")
    STORAGE = EsField("storage", name="仓库", es_type="string")  # 总仓等
    QUANTITY_TYPE = EsField("quantityType", name="库存种类", es_type="string") # 1，2
    UPLOAD_RATIO = EsField("uploadRatio", name="库存比例", es_type="string")
    VIRTUAL_INVENTORY = EsField("virtualInventory", name="虚拟库存", es_type="string")
    SYNC_TIME = EsField("syncTime", name="同步时间", es_type="date")

    def __init__(self):
        super(EsInventoryRatio, self).__init__()
        self.cli = es_cli
        self.index = 'inventory_ratio'
        self.test_index = 'inventory_ratio_test'
        self.doc_type = 'data'
        self.primary_keys = [self.SKU_BARCODE, self.CHANNEL, self.STORAGE]

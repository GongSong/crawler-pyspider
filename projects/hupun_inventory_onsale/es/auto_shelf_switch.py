from pyspider.core.model.es_base import *


class EsAutoShelfSwitch(Base):
    ''' 小红书和app的sku_barcode用渠道id，其余用内部id '''
    SKU_BARCODE = EsField("fakeSku", name="虚构SKU号", es_type="string")  # 唯品会为真实sku，其余渠道sku是与spu相同的虚构sku
    SPU_BARCODE = EsField("spuBarcode", name="SPU号", es_type="string")  # 内部id
    CHANNEL_PRODUCT_ID = EsField("channelProductId", name="渠道商品id", es_type="string")  # 渠道id
    CHANNEL = EsField("channel", name="渠道", es_type="string")  # 天猫、天猫奥莱店、小红书、唯品会
    SYNC_TIME = EsField("syncTime", name="同步时间", es_type="date")
    SWITCH_STATUS = EsField("switchStatus", name="自动上架开关状态", es_type="string")  # 开/关/部分开

    def __init__(self):
        super(EsAutoShelfSwitch, self).__init__()
        self.cli = es_cli
        self.index = 'auto_shelf_switch'
        self.test_index = 'auto_shelf_switch_test'
        self.doc_type = 'data'
        self.primary_keys = [self.SKU_BARCODE, self.CHANNEL]

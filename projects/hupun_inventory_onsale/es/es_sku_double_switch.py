from pyspider.core.model.es_base import *


class EsSkuDoubleSwitch(Base):
    SKU_BARCODE = EsField("skuBarcode", name="SKU号", es_type="string")
    SPU_BARCODE = EsField("spuBarcode", name="SPU号", es_type="string")
    CHANNEL = EsField("channel", name="渠道", es_type="string")  # 天猫、奥莱店、小红书、唯品会
    SYNC_TIME = EsField("syncTime", name="同步时间", es_type="date")
    SWITCH_STATUS = EsField("switchStatus", name="自动上架开关状态", es_type="string")  # 开/关
    INVENTORY_SWITCH_STATUS = EsField("inventorySwitchStatus", name="上传库存开关状态", es_type="string")  # 开/关
    SYNC_STATUS = EsField("syncStatus", name="同步状态", es_type="string")
    FAIL_REASON = EsField("failReason", name="失败原因", es_type="string")

    def __init__(self):
        super(EsSkuDoubleSwitch, self).__init__()
        self.cli = es_cli
        self.index = 'sku_double_switch'
        self.test_index = 'sku_double_switch_test'
        self.doc_type = 'data'
        self.primary_keys = [self.SKU_BARCODE, self.CHANNEL]

from pyspider.core.model.es_base import *


class EsDoubleSwitchStatus(Base):
    SPU_BARCODE = EsField("spuBarcode", name="SPU号", es_type="string")  # 内部id
    CHANNEL = EsField("channel", name="渠道", es_type="string")  # 天猫、奥莱店、小红书、唯品会
    GOODS_ID = EsField("goodsId", name="商品ID", es_type="string")  # 渠道id
    SYNC_STATUS = EsField("syncStatus", name="同步状态", es_type="string")
    FAIL_REASON = EsField("failReason", name="失败原因", es_type="string")
    # 对比操作时间，同步最近一天的数据
    SYNC_TIME = EsField("syncTime", name="同步时间", es_type="date")

    def __init__(self):
        super(EsDoubleSwitchStatus, self).__init__()
        self.cli = es_cli
        self.index = 'double_switch_status'
        self.test_index = 'double_switch_status_test'
        self.doc_type = 'data'
        self.primary_keys = [self.SPU_BARCODE, self.CHANNEL]

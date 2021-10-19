from pyspider.core.model.es_base import *


class EsShelfObtainedStatus(Base):
    SPU_BARCODE = EsField("spuBarcode", name="SPU号", es_type="string")  # 内部id
    CHANNEL = EsField("channel", name="渠道", es_type="string")  # 天猫、天猫奥莱店、小红书、唯品会
    GOODS_ID = EsField("goodsId", name="商品ID", es_type="string")  # 渠道id
    SHELF_STATUS = EsField("shelfStatus", name="上下架状态", es_type="string")
    SYNC_STATUS = EsField("syncStatus", name="同步状态", es_type="string")
    FAIL_REASON = EsField("failReason", name="失败原因", es_type="string")
    INVENTORY = EsField("inventory", name="库存", es_type="sum")
    # 对比操作时间，同步最近一天的数据
    SYNC_TIME = EsField("syncTime", name="同步时间", es_type="date")

    def __init__(self):
        super(EsShelfObtainedStatus, self).__init__()
        self.cli = es_cli
        self.index = 'goods_shelf_obtained'
        self.test_index = 'goods_shelf_obtained_test'
        self.doc_type = 'data'
        self.primary_keys = [self.SPU_BARCODE, self.CHANNEL]

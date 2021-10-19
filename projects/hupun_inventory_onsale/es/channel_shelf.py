from pyspider.core.model.es_base import *

class EsChannelShelf(Base):
    SPU_BARCODE = EsField("spuBarcode", name="SPU号", es_type="string")
    IMAGE_URL = EsField("imageUrl", name="图片链接", es_type="string")
    NAME = EsField("name", name="商品名称", es_type="string")
    ERP_INVENTORY = EsField('erpInventory', name='销售库存', es_type='sum', comment='用于销售的仓库的可用+在途的库存总量')
    SELL_AVAILABLE_SIZE = EsField('sellAvailableSize', name='可用库存', es_type='sum', comment='销售仓库的商品已入仓的可用库存量')
    SELL_UNDERWAY = EsField('sellUnderway', name='在途库存', es_type='sum', comment='销售仓库的商品还在途未入仓的商品库存量')
    # SKU_BARCODE_LIST = EsField("skuBarcodeList", name="所有sku号")
    FIRST_AUDIT_TIME = EsField("firstAuditTime", name="上架时间", es_type="string")

    APP_GOODS_ID = EsField("appGoodsId", name='app渠道的商品ID', es_type="string")
    TMALL_GOODS_ID = EsField("tmallGoodsId", name='天猫渠道的商品ID', es_type="string")
    WEI_GOODS_ID = EsField("weiGoodsId", name="唯品会渠道的商品ID", es_type="string")
    OTLS_GOODS_ID = EsField("otlsGoodsId", name="天猫奥莱店渠道的商品ID", es_type="string")
    RED_BOOK_GOODS_ID = EsField("productId", name="小红书渠道商品ID", es_type="string")
    RED_BOOK_GOODS_NAME = EsField("redbookGoodsName", name="小红书商品名称", es_type="string")

    APP_INVENTORY = EsField("appInventory", name="app渠道的库存", es_type="sum")
    TMALL_INVENTORY = EsField("tmallInventory", name="天猫渠道的库存", es_type="sum")
    WEI_INVENTORY = EsField("weiInventory", name="唯品会渠道的库存", es_type="sum")
    OTLS_INVENTORY = EsField("otlsInventory", name="天猫奥莱店渠道的库存", es_type="sum")
    RED_BOOK_INVENTORY = EsField("redbookInventory", name="小红书渠道的库存", es_type="sum")

    APP_SHELF_STATUS = EsField("appShelfStatus", name="app渠道的上下架状态", es_type="string")
    TMALL_SHELF_STATUS = EsField("tmallShelfStatus", name="天猫渠道的上下架状态", es_type="string")
    WEI_SHELF_STATUS = EsField("weiShelfStatus", name="唯品会渠道的上下架状态", es_type="string")
    OTLS_SHELF_STATUS = EsField("otlsShelfStatus", name="天猫奥莱店渠道的上下架状态", es_type="string")
    RED_BOOK_SHELF_STATUS = EsField("redbookShelfStatus", name="小红书渠道的上下架状态", es_type="string")

    APP_SYNC_STATUS = EsField("appSyncStatus", name="app渠道的同步状态", es_type="string")
    TMALL_SYNC_STATUS = EsField("tmallSyncStatus", name="天猫渠道的同步状态", es_type="string")
    WEI_SYNC_STATUS = EsField("weiSyncStatus", name="唯品会渠道的同步状态", es_type="string")
    OTLS_SYNC_STATUS = EsField("otlsSyncStatus", name="天猫奥莱店渠道的同步状态", es_type="string")
    RED_BOOK_SYNC_STATUS = EsField("redbookSyncStatus", name="小红书渠道的同步状态", es_type="string")

    APP_FAIL_REASON = EsField("appFailReason", name="app渠道的同步失败原因", es_type="string")
    TMALL_FAIL_REASON = EsField("tmallFailReason", name="天猫渠道的同步失败原因", es_type="string")
    WEI_FAIL_REASON = EsField("weiFailReason", name="唯品会渠道的同步失败原因", es_type="string")
    OTLS_FAIL_REASON = EsField("otlsFailReason", name="天猫奥莱店渠道的同步失败原因", es_type="string")
    RED_BOOK_FAIL_REASON = EsField("redbookFailReason", name="小红书渠道的同步失败原因", es_type="string")

    TMALL_SYNC_TIME = EsField("tmallSyncTime", name="天猫渠道的同步时间", es_type="string")
    WEI_SYNC_TIME = EsField("weiSyncTime", name="唯品会渠道的同步时间", es_type="string")
    OTLS_SYNC_TIME = EsField("otlsSyncTime", name="天猫奥莱店渠道的同步时间", es_type="string")
    RED_BOOK_SYNC_TIME = EsField("redbookSyncTime", name="小红书渠道的同步时间", es_type="string")

    def __init__(self):
        super(EsChannelShelf, self).__init__()
        self.cli = es_cli
        self.index = 'channel_shelf'
        self.test_index = 'channel_shelf_test'
        self.doc_type = 'data'
        self.primary_keys = [self.SPU_BARCODE]

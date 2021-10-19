from pyspider.core.model.es_base import *


class InventorySync(Base):
    """
    库存同步 的数据
    """
    SPU_BARCODE = EsField("spuBarcode", name="spu号, 如果是只同步sku, 它就是sku号", es_type="string")
    SYNC_TIME = EsField("syncTime", name="同步失败时间", es_type="string")
    FAIL_REASON = EsField("failReason", name="失败原因", es_type="string")
    SYNC_STATUS = EsField("syncStatus", name="同步状态, 0,成功;1,失败,2,同步中", es_type="string")
    FLAG = EsField("flag", name="用来区分是sku还是spu同步, sku, spu", es_type="string")

    def __init__(self):
        super(InventorySync, self).__init__()
        self.cli = es_cli
        self.index = 'goods_error_msg'
        self.test_index = 'goods_error_msg_test'
        self.doc_type = 'data'
        self.primary_keys = [self.SPU_BARCODE]

    def get_all_spu_barcode(self):
        """
        获取所有的spuBarcode
        :return:
        """
        query = EsQueryBuilder().term('syncStatus', '1').source(['spuBarcode'])
        return self.scroll(query)

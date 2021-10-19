from pyspider.core.model.es_base import *


class EsAllocateBill(Base):
    ''' 库存调拨单 '''
    BILL_CODE = EsField("bill_code", name="调拨单号", es_type="string")
    SYNC_TIME = EsField("syncTime", name="同步时间", es_type="date")

    def __init__(self):
        super(EsAllocateBill, self).__init__()
        self.cli = es_cli
        self.index = 'allocate_bill'
        self.test_index = 'allocate_bill_test'
        self.doc_type = 'data'
        self.primary_keys = [self.BILL_CODE]

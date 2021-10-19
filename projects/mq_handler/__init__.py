from hupun_inventory_onsale.change_inventory_status import ChangeInventoryStatus
from hupun_inventory_onsale.allocate_inventory_bill import AllocateInvBill
from mq_handler.blog_last_update_inform import BlogUpInform
from mq_handler.blog_sync_account import BlogSyncAct
from mq_handler.category_delete import CategoryDelete
from mq_handler.category_drag import CategoryDrag
from mq_handler.category_result import CategoryResult
from mq_handler.category_update import CategoryUpdate
from mq_handler.erp_goods.goods_relation import GoodsRelation
from mq_handler.hupun_stock_bills.add_appointment_receipt import AddAppointmentReceipt
from mq_handler.hupun_stock_bills.add_receipt import AddReceipt
from mq_handler.hupun_stock_bills.add_outbound import AddOutbound
from mq_handler.hupun_stock_bills.close_appointment_outbound_mq import CloseAppOutboundMq
from mq_handler.inventory_operation.inv_common_config import InvCommonConfig
from mq_handler.inventory_operation.inv_sync_manual import InvSyncManual
from mq_handler.order.order_sku_rename import OrderSkuRename
from mq_handler.order.order_split import OrderSplit
from mq_handler.print import Print
from mq_handler.purchase_order_add import PurchaseOrderAdd
from mq_handler.purchase_order_add_result import PurOrAdResult
from mq_handler.purchase_order_arrive_count import PurOrArrCount
from mq_handler.purchase_order_close import PurOrderClose
from mq_handler.purchase_order_close_add import PurOrderCloseAdd
from mq_handler.purchase_order_close_result import PurOrClResult
from mq_handler.purchase_stock_add import PurchaseStockAdd
from mq_handler.erp_goods.sync_erp_goods import SyncErpGoods
from mq_handler.erp_goods.sync_erp_goods_result import SyncErpGoodsResult
from mq_handler.purchase_whole_order_close import PurWholeOrderClose
from mq_handler.purchase_whole_order_close_result import PurchaseWholeClResult
from mq_handler.sync_erp_supplier import SyncErpSupplier
from mq_handler.sync_erp_supplier_result import SyncErpSupplierResult
from mq_handler.sync_erp_warehouse import SyncErpWarehouse
from mq_handler.table_download import TableDownload
from mq_handler.hupun_stock_bills.add_appointment_outbound import AddAppointmentOutbound
from mq_handler.warehouse.warehouse_store_set import WarehouseStoreSet

CONST_MESSAGE_TAG_PRINT = 'print'
CONST_MESSAGE_TAG_TABLE_DOWNLOAD_COMPLETED = 'table_download'  # 表格下载完成的 tag
CONST_MESSAGE_TAG_SYNC_ERP_GOODS = 'syncErpGoods'  # erp商品同步的 tag
CONST_MESSAGE_TAG_SYNC_ERP_GOODS_RESULT = 'syncGoodsResult'  # erp商品同步返回结果的 tag
CONST_MESSAGE_TAG_SYNC_ERP_SUPPLIER = 'supplier'  # erp供应商同步的 tag
CONST_MESSAGE_TAG_SYNC_ERP_SUPPLIER_RESULT = 'supplierResult'  # erp供应商同步回结果的 tag
CONST_MESSAGE_TAG_SYNC_ERP_WAREHOUSE = 'saveErpWarehouse' # erp仓库同步tag
CONST_MESSAGE_TAG_CATEGORY_UPDATE = 'updateCate'  # erp 类目的更新(添加，编辑) tag
CONST_MESSAGE_TAG_CATEGORY_DRAG = 'dragCate'  # erp 类目的拖拽 tag
CONST_MESSAGE_TAG_CATEGORY_DELETE = 'deleteCate'  # erp 类目的删除 tag
CONST_MESSAGE_TAG_CATEGORY_RESULT = 'updateCateResult'  # erp 类目传递消息的 tag
CONST_MESSAGE_TAG_PURCHARSE_ADD = 'addPurchase'  # 添加采购订单的tag
CONST_MESSAGE_TAG_PURCHARSE_ADD_RE = 'addPurResult'  # 添加采购订单返回数据的tag
CONST_MESSAGE_TAG_PURCHARSE_CLOSE = 'closeDocumentary'  # 关闭采购订单的tag
CONST_MESSAGE_TAG_PURCHARSE_CLOSE_RE = 'closeDocuResult'  # 关闭采购订单的返回数据tag
CONST_MESSAGE_TAG_PURCHARSE_ARRIVE_COUNT = 'getArriveCount'  # 采购订单的到仓数据tag
CONST_MESSAGE_TAG_PURCHARSE_STOCK_ADD = 'updateWarehouse'  # 采购入库单的添加tag
CONST_MESSAGE_TAG_PURCHARSE_STOCK_RESULT = 'updateWareRes'  # 采购入库单的添加后返回数据tag
CONST_MESSAGE_TAG_BLOG_SYNC_ACT = 'syncBlogAccount'  # 同步微博和ins的账号tag
CONST_MESSAGE_TAG_BLOG_RESULT = 'blogResult'  # 同步微博和ins的账号后返回抓取完成的通知tag
CONST_MESSAGE_TAG_BLOG_UP_INFORM = 'upLastBlogTime'  # 更新微博和ins的账号后通知服务端本次抓取时间tag
CONST_MESSAGE_TAG_SHELF_STATUS = 'syncShelfObtain'  # 设置商品上下架状态tag
CONST_MESSAGE_TAG_UPDATE_CHANNEL_INVENTORY = "updateChanInv"  # 手动更新各渠道库存tag
CONST_MESSAGE_TAG_SYNC_COMMON_INV = "syncCommonInv"  # ERP通用库存同步配置tag
CONST_MESSAGE_TAG_UPDATE_GOODS_RELATION = "updateRelation"  # ERP更新店铺商品对应关系tag
CONST_MESSAGE_TAG_DOUBLE_SWITCH = 'syncDoubleSwitch'  # 设置商品erp的【上传库存】【自动上架】开关tag
CONST_MESSAGE_TAG_SYNC_INVENTORY_RATIO = 'syncInvRatio'  # 更新商品库存比例tag
CONST_MESSAGE_TAG_CLEAR_INVENTORY_RATIO = 'clearInvRatio'  # 清除商品库存比例tag
CONST_MESSAGE_TAG_ORDER_SPLIT = 'divideOrder'  # 订单的拆单tag
CONST_MESSAGE_TAG_ORDER_SKU_RENAME = 'skuRename'  # 订单审核界面的商品sku重命名tag
CONST_MESSAGE_TAG_SYNC_SKU_INVENTORY_RATIO = 'setSkuInvRatio'  # 设置商品sku级别库存比例tag
CONST_MESSAGE_TAG_SKU_DOUBLE_SWITCH = 'setSkuSwitch'  # 设置商品sku级别【上传库存】【自动上架】开关tag
CONST_MESSAGE_TAG_CLEAR_SKU_INVENTORY_RATIO = 'clearSkuRatio'  # 清除商品sku级别库存比例tag
CONST_MESSAGE_TAG_WAREHOUSE_STORE_SET = 'ChaInvRelation'  # 例外店铺设置更改店铺和仓库对应关系的tag
CONST_MESSAGE_TAG_ADD_ALLOCATE_INVENTORY = 'addAllocateInv'  # 新增调拨单并审核tag
CONST_MESSAGE_TAG_PURCHARSE_WHOLE_CLOSE = 'closePurchase'  # 整单关闭采购订单的tag
CONST_MESSAGE_TAG_PURCHARSE_WHOLE_CLOSE_RE = 'closePurResult'  # 整单关闭采购订单的返回数据tag
CONST_MESSAGE_TAG_ADD_APPOINTMRNT_OUTBOUND = 'addAppOutbound'   # 创建预约发货单tag
CONST_MESSAGE_TAG_ADD_APPOINTMRNT_OUTBOUND_RE = 'addAppOutboundRe'  # 创建预约发货单返回信息tag
CONST_MESSAGE_TAG_ADD_OUTBOUND_API = 'addOutboundApi'   # 创建发货单tag
CONST_MESSAGE_TAG_ADD_APPOINTMRNT_INVOICE = 'addAppInvoice'   # 创建预约入库单tag
CONST_MESSAGE_TAG_ADD_INVOICE = 'addInvoice'   # 创建入库单tag
CONST_MESSAGE_TAG_CLOSE_APP_OUTBOUND = 'closeAppOutbound'  # 关闭预约出库单
CONST_MESSAGE_TAG_CLOSE_ADD_PURCHASE = 'closeAddPurchase'  # 关闭并添加采购单


CONST_ACTION_CREATE = 'create'
CONST_ACTION_UPDATE = 'update'
CONST_ACTION_DELETE = 'delete'

message_tag_to_handler = {
    CONST_MESSAGE_TAG_PRINT: Print,
    CONST_MESSAGE_TAG_TABLE_DOWNLOAD_COMPLETED: TableDownload,
    CONST_MESSAGE_TAG_SYNC_ERP_GOODS: SyncErpGoods,
    CONST_MESSAGE_TAG_SYNC_ERP_GOODS_RESULT: SyncErpGoodsResult,
    CONST_MESSAGE_TAG_SYNC_ERP_SUPPLIER: SyncErpSupplier,
    CONST_MESSAGE_TAG_SYNC_ERP_SUPPLIER_RESULT: SyncErpSupplierResult,
    CONST_MESSAGE_TAG_SYNC_ERP_WAREHOUSE: SyncErpWarehouse,
    CONST_MESSAGE_TAG_CATEGORY_UPDATE: CategoryUpdate,
    CONST_MESSAGE_TAG_CATEGORY_DRAG: CategoryDrag,
    CONST_MESSAGE_TAG_CATEGORY_DELETE: CategoryDelete,
    CONST_MESSAGE_TAG_CATEGORY_RESULT: CategoryResult,
    CONST_MESSAGE_TAG_PURCHARSE_ADD: PurchaseOrderAdd,
    CONST_MESSAGE_TAG_PURCHARSE_ADD_RE: PurOrAdResult,
    CONST_MESSAGE_TAG_PURCHARSE_CLOSE: PurOrderClose,
    CONST_MESSAGE_TAG_PURCHARSE_CLOSE_RE: PurOrClResult,
    CONST_MESSAGE_TAG_PURCHARSE_WHOLE_CLOSE: PurWholeOrderClose,
    CONST_MESSAGE_TAG_PURCHARSE_WHOLE_CLOSE_RE: PurchaseWholeClResult,
    CONST_MESSAGE_TAG_PURCHARSE_ARRIVE_COUNT: PurOrArrCount,
    CONST_MESSAGE_TAG_BLOG_SYNC_ACT: BlogSyncAct,
    # CONST_MESSAGE_TAG_BLOG_RESULT: BlogUpInform,
    CONST_MESSAGE_TAG_PURCHARSE_STOCK_ADD: PurchaseStockAdd,
    CONST_MESSAGE_TAG_UPDATE_CHANNEL_INVENTORY: InvSyncManual,
    CONST_MESSAGE_TAG_SYNC_COMMON_INV: InvCommonConfig,
    CONST_MESSAGE_TAG_UPDATE_GOODS_RELATION: GoodsRelation,
    CONST_MESSAGE_TAG_ORDER_SPLIT: OrderSplit,
    CONST_MESSAGE_TAG_ORDER_SKU_RENAME: OrderSkuRename,
    CONST_MESSAGE_TAG_WAREHOUSE_STORE_SET: WarehouseStoreSet,
    CONST_MESSAGE_TAG_ADD_ALLOCATE_INVENTORY: AllocateInvBill,
    CONST_MESSAGE_TAG_SHELF_STATUS: ChangeInventoryStatus,
    CONST_MESSAGE_TAG_ADD_APPOINTMRNT_OUTBOUND: AddAppointmentOutbound,
    CONST_MESSAGE_TAG_ADD_OUTBOUND_API: AddOutbound,
    CONST_MESSAGE_TAG_ADD_APPOINTMRNT_INVOICE: AddAppointmentReceipt,
    CONST_MESSAGE_TAG_ADD_INVOICE: AddReceipt,
    CONST_MESSAGE_TAG_CLOSE_APP_OUTBOUND: CloseAppOutboundMq,
    CONST_MESSAGE_TAG_CLOSE_ADD_PURCHASE: PurOrderCloseAdd
}

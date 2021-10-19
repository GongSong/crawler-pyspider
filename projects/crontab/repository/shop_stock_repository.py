"""
门店库存相关的数据处理层
"""
from crontab.model.mysql.order_goods import OrderGoods
from crontab.model.mysql.order_info import OrderInfo
from crontab.model.mysql.product import Product
from crontab.model.mysql.shop import Shop
from crontab.model.mysql.sku_unit_cost.base_order_goods import BaseOrderGoods
from crontab.model.mysql.sku_unit_cost.based_refund_order_goods import BaseRefundOrderGoods
from crontab.model.mysql.sku_unit_cost.offline_order import OfflineOrder
from crontab.model.mysql.sku_unit_cost.offline_order_goods import OfflineOrderGoods
from crontab.model.mysql.sku_unit_cost.offline_refund import OfflineRefund
from crontab.model.mysql.sku_unit_cost.offline_refund_goods import OfflineRefundGoods
from crontab.model.mysql.sku_unit_cost.purchase_order import PurchaseOrder
from crontab.model.mysql.sku_unit_cost.purchase_order_goods import PurchaseOrderGoods
from crontab.model.mysql.sku_unit_cost.purchase_order_goods_count import PurchaseOrderGoodsCount
from crontab.model.mysql.sku_unit_cost.purchase_refund import PurchaseRefund
from crontab.model.mysql.sku_unit_cost.purchase_refund_goods import PurchaseRefundGoods
from crontab.model.mysql.sku_unit_cost.purchase_sku import PurchaseSku
from crontab.model.mysql.warehouse import Warehouse
from hupun_inventory.model.es.goods_inventory_sku import GoodsInventorySku
from mysql_async.model.mysql.whole_inout_order import WholeInoutOrder
from pyspider.helper.date import Date
from pyspider.helper.es_query_builder import EsQueryBuilder


def get_product_total(filter_warehouse_ids: list) -> dict:
    """
    获取所有门店仓的商品库存
    eg: {
        51: { # 仓库ID
            '21021C0013G161': {
                "actual_stock": 1, # 实际库存
                "underway_stock": 1, # 在途库存
                "lock_stock": 1, # 锁定库存
                "available_stock": 1, # 可用库存
            }
        }
    }
    :rtype: object
    """
    goods_map = {}
    res = [_ for _ in Product.select().where((Product.warehouse_id << filter_warehouse_ids) & ((Product.actual_stock != 0) |
                   (Product.underway_stock != 0) | (Product.lock_stock != 0) | (Product.available_stock != 0))).dicts()]
    for item in res:
        sku = item.get("sku", "")
        warehouse_id = item.get("warehouse_id", 0)
        stock_item = {
            "actual_stock": item.get("actual_stock", 0),  # 实际库存
            "underway_stock": item.get("underway_stock", 0),  # 在途库存
            "lock_stock": item.get("lock_stock", 0),  # 锁定库存
            "available_stock": item.get("available_stock", 0),  # 可用库存
        }
        if goods_map.get(warehouse_id):
            goods_map.get(warehouse_id).setdefault(sku, stock_item)
        else:
            goods_map[warehouse_id] = {sku: stock_item}
    return goods_map


def get_warehouse_shop_by_types(types: list) -> (list, dict):
    """
    获取指定类型的仓库和门店ID
    :return:
    """
    # 仓库id列表
    warehouses = []
    # 仓库和店铺的id映射
    warehouse_shop_map = {}
    res = [_ for _ in Warehouse.select().where(Warehouse.type << types).dicts()]
    for item in res:
        warehouses.append(item.get("warehouse_id", 0))
        warehouse_shop_map[item.get("warehouse_id", 0)] = item.get("related_id", 0)
    return warehouses, warehouse_shop_map


def get_shop_types_by_ids(shop_ids: list) -> dict:
    """
    获取仓库对应门店的类型：0:直营, 1:加盟, 2:联营
    :param shop_ids:
    :return:
    """
    type_map = {}
    res = [_ for _ in Shop.select().where(Shop.shop_id << shop_ids).dicts()]
    for item in res:
        type_map.setdefault(item.get("shop_id", 0), item.get("shop_type", 0))
    return type_map


def get_inout_order_stock(base_time=0) -> dict:
    """
    获取所有出入库明细
    :param base_time: 基准时间，从这个时间开始获取出入库明细；为 0 则获取所有的出入库明细
    :return: eg: {"出入库id": 仓库ID}
    """
    order_map = {}
    if base_time > 0:
        result = OrderInfo.select().where(OrderInfo.create_time > base_time).dicts()
    else:
        result = OrderInfo.select().dicts()
    res = [_ for _ in result]
    for item in res:
        order_id = item.get("code", "")
        warehouse_id = item.get("warehouse_id", 0)
        order_map.setdefault(order_id, warehouse_id)
    return order_map


def get_inout_order_goods_map(order_ids: list) -> dict:
    """
    获取出入库单据对应的出入库商品的map
    eg: {
        "DBRK202005300002": {
            "1952D00054W305": 1,
            "1952D00050W172": -1,
        }
    }
    :return:
    """
    order_goods_sku_map = {}
    res = [_ for _ in OrderGoods.select().where(OrderGoods.order_id << order_ids).dicts()]
    for item in res:
        sku = item.get("sku_id", "")
        order_id = item.get("order_id", "")
        count = item.get("count", 0)
        if order_goods_sku_map.get(order_id, {}):
            if "CK" in order_id:
                order_goods_sku_map.get(order_id, {})[sku] = -count
            else:
                order_goods_sku_map.get(order_id, {})[sku] = count
        else:
            if "CK" in order_id:
                order_goods_sku_map.setdefault(order_id, {})[sku] = -count
            else:
                order_goods_sku_map.setdefault(order_id, {})[sku] = count
    return order_goods_sku_map


def get_online_product_total(warehouse_ids: list):
    """
    获取所有线上仓库的实时商品库存
    eg: {
        "FBA807A72474376E8CFBBE9848F271B2": { # 仓库ID
            '21021C0013G161': {
                "actual_stock": 1, # 实际库存
                "underway_stock": 1, # 在途库存
                "lock_stock": 1, # 锁定库存
                "available_stock": 1, # 可用库存
            }
        }

    :param warehouse_ids: 万里牛的仓库id(长度32位)
    :return:
    """
    # availableSize: 可用；quantity：实际； 锁定：lock；在途:
    # 如果四个库存全部为0，则过滤掉
    sku_list = GoodsInventorySku().scroll(EsQueryBuilder()
                                          .terms('storageID.keyword', warehouse_ids)
                                          .must_not(EsQueryBuilder()
                                                    .must(EsQueryBuilder()
                                                          .term("quantity", 0)
                                                          .term("underway", 0)
                                                          .term("lock", 0)
                                                          .term("availableSize", 0)))
                                          .source(
        ['storageID', 'spec_code', 'availableSize', 'quantity', 'lock', 'underway']))
    goods_map = {}
    for sku_item in sku_list:
        for item in sku_item:
            warehouse_id = item['storageID']
            sku = item['spec_code']
            stock_item = {
                "actual_stock": item.get("quantity", 0),  # 实际库存
                "underway_stock": item.get("underway", 0),  # 在途库存
                "lock_stock": item.get("lock", 0),  # 锁定库存
                "available_stock": item.get("availableSize", 0),  # 可用库存
            }
            if goods_map.get(warehouse_id):
                goods_map.get(warehouse_id).setdefault(sku, stock_item)
            else:
                goods_map[warehouse_id] = {sku: stock_item}
    return goods_map


def get_online_inout_order_stock(base_time=0) -> dict:
    """
    获取所有万里牛erp线上的出入库明细
    :param base_time: 基准时间，从这个时间开始获取出入库明细；为 0 则获取所有的出入库明细
    :return: eg: {"出入库id": 仓库ID, }
    """
    order_map = {}
    if base_time:
        result = WholeInoutOrder.select().where(WholeInoutOrder.bill_time > base_time).dicts()
    else:
        result = WholeInoutOrder.select().dicts()
    res = [_ for _ in result]
    for item in res:
        order_id = item.get("bill_code", "")
        warehouse_id = item.get("storage_id", "")
        order_map.setdefault(order_id, warehouse_id)
    return order_map


def get_online_inout_order_goods_map(order_ids: list) -> dict:
    """
    获取出入库单据对应的出入库商品的map
    eg: {
        "XC210815000032": {
            "1952D00054W305": 1,
            "1952D00050W172": -1,
        }
    }
    :return:
    """
    order_goods_sku_map = {}
    res = [_ for _ in WholeInoutOrder.select().where(WholeInoutOrder.bill_code << order_ids).dicts()]
    for item in res:
        sku = item.get("sku", "")
        order_id = item.get("bill_code", "")
        count = item.get("in_or_out", 0)
        if order_goods_sku_map.get(order_id, {}):
            order_goods_sku_map.get(order_id, {})[sku] = count
        else:
            order_goods_sku_map.setdefault(order_id, {})[sku] = count
    return order_goods_sku_map


def get_online_sale_out(base_time=0) -> dict:
    """
    获取线上的商品销售出库数据,商品的出库时间和出库数量的map
    出库的count全部为负
    :return: {
        15978238974 : { // 时间戳
            "2031A00010C161": { // sku
                "price": 23.23,  // 单价
                "count": 3      // 数量，正：入库；负：出库
            }
        }
    }
    """
    goods_map = {}
    if base_time > 0:
        res = [_ for _ in BaseOrderGoods.select().where(BaseOrderGoods.paid_time < Date(base_time).format()).dicts()]
    else:
        res = [_ for _ in BaseOrderGoods.select().dicts()]

    for item in res:
        sku = item.get("sku", "")
        count = abs(item.get("sold_count", 0))
        whole_price = float(item.get("paid_price", 0))
        price = round(whole_price / count, 2) if count > 0 else 0
        timestamp = Date(item.get("paid_time")).timestamp() if item.get("paid_time") else 0
        sku_item = {
            "price": price,
            "count": -count
        }
        if goods_map.get(timestamp, {}):
            goods_map.get(timestamp, {}).setdefault(sku, sku_item)
        else:
            goods_map.setdefault(timestamp, {})[sku] = sku_item
    return goods_map


def get_online_refund(goods_map: dict, base_time=0):
    """
    获取线上的商品销售退货数据,商品的退货时间和出库数量的map
    退货的count全部为正
    :goods_map: 商品map
    :return: {
        15978238974 : { // 时间戳
            "2031A00010C161": { // sku
                "price": 23.23,  // 单价
                "count": 3      // 数量，正：入库；负：出库
            }
        }
    }
    """
    if base_time > 0:
        res = [_ for _ in BaseRefundOrderGoods.select().where(BaseRefundOrderGoods.refund_time < Date(base_time).format()).dicts()]
    else:
        res = [_ for _ in BaseRefundOrderGoods.select().dicts()]

    for item in res:
        sku = item.get("sku", "")
        count = abs(item.get("refund_count", 0))
        whole_price = float(item.get("refund_price", 0))
        price = round(whole_price / count, 2) if count > 0 else 0
        timestamp = Date(item.get("refund_time")).timestamp() if item.get("refund_time") else 0
        sku_item = {
            "price": price,
            "count": count
        }
        if goods_map.get(timestamp, {}):
            origin_sku_item = goods_map.get(timestamp, {}).get(sku, {})
            origin_sku_price = origin_sku_item.get("price", 0)
            origin_sku_count = origin_sku_item.get("count", 0)
            now_sku_price = round((whole_price + origin_sku_price * origin_sku_count) / (count + origin_sku_count),
                                  2) if count + origin_sku_count > 0 else 0
            now_sku_item = {
                "price": now_sku_price,
                "count": origin_sku_count + count
            }
            goods_map.get(timestamp, {})[sku] = now_sku_item
        else:
            goods_map.setdefault(timestamp, {})[sku] = sku_item


def get_offline_sale_out(goods_map: dict, base_time=0):
    """
    获取线下的商品销售出库数据
    出库的count全部为负
    :goods_map: 商品map
    :return: {
        15978238974 : { // 时间戳
            "2031A00010C161": { // sku
                "price": 23.23,  // 单价
                "count": 3      // 数量，正：入库；负：出库
            }
        }
    }
    """
    if base_time > 0:
        res = [_ for _ in OfflineOrder.select(
            OfflineOrder.pay_time, OfflineOrderGoods.sku, OfflineOrderGoods.count, OfflineOrderGoods.final_price
        ).where(OfflineOrder.pay_time < base_time).join(
            OfflineOrderGoods, on=(OfflineOrder.order_id == OfflineOrderGoods.order_id)).dicts()]
    else:
        res = [_ for _ in OfflineOrder.select(
            OfflineOrder.pay_time, OfflineOrderGoods.sku, OfflineOrderGoods.count, OfflineOrderGoods.final_price
        ).join(OfflineOrderGoods, on=(OfflineOrder.order_id == OfflineOrderGoods.order_id)).dicts()]
    for item in res:
        sku = item.get("sku", "")
        count = abs(item.get("count", 0))
        whole_price = float(item.get("final_price", 0))
        price = round(whole_price / count, 2) if count > 0 else 0
        timestamp = Date(item.get("pay_time")).timestamp() if item.get("pay_time") else 0
        sku_item = {
            "price": price,
            "count": -count
        }
        if goods_map.get(timestamp, {}):
            goods_map.get(timestamp, {}).setdefault(sku, sku_item)
        else:
            goods_map.setdefault(timestamp, {})[sku] = sku_item


def get_offline_refund(goods_map: dict, base_time=0):
    """
    获取线下的商品销售退货数据
    退货的count全部为正
    :goods_map: 商品map
    :return: {
        15978238974 : { // 时间戳
            "2031A00010C161": { // sku
                "price": 23.23,  // 单价
                "count": 3      // 数量，正：入库；负：出库
            }
        }
    }
    """
    if base_time > 0:
        res = [_ for _ in OfflineRefund.select(
            OfflineRefundGoods.sku, OfflineRefundGoods.count, OfflineRefundGoods.cash,
            OfflineRefundGoods.balance, OfflineRefund.refund_time
        ).where(OfflineRefund.refund_time < Date(base_time).format()).join(
            OfflineRefundGoods, on=(OfflineRefund.refund_id == OfflineRefundGoods.refund_id)).dicts()]
    else:
        res = [_ for _ in OfflineRefund.select(
            OfflineRefundGoods.sku, OfflineRefundGoods.count, OfflineRefundGoods.cash,
            OfflineRefundGoods.balance, OfflineRefund.refund_time
        ).join(OfflineRefundGoods, on=(OfflineRefund.refund_id == OfflineRefundGoods.refund_id)).dicts()]
    for item in res:
        sku = item.get("sku", "")
        count = abs(int(item.get("count", 0))) if item.get("count") else 0
        whole_price = float(item.get("cash", 0) + item.get("balance", 0))
        price = round(whole_price / count, 2) if count > 0 else 0
        timestamp = Date(item.get("refund_time")).timestamp() if item.get("refund_time") else 0
        sku_item = {
            "price": price,
            "count": count
        }
        if goods_map.get(timestamp, {}):
            origin_sku_item = goods_map.get(timestamp, {}).get(sku, {})
            origin_sku_price = origin_sku_item.get("price", 0)
            origin_sku_count = origin_sku_item.get("count", 0)
            now_sku_price = round((whole_price + origin_sku_price * origin_sku_count) / (count + origin_sku_count),
                                  2) if count + origin_sku_count > 0 else 0
            now_sku_item = {
                "price": now_sku_price,
                "count": origin_sku_count + count
            }
            goods_map.get(timestamp, {})[sku] = now_sku_item
        else:
            goods_map.setdefault(timestamp, {})[sku] = sku_item


def get_purchase_sku_map():
    """
    获取采购商品的skuid和skubarcode的map
    :return:
    """
    return {item.get("skuId", ""): item.get("skuBarcode", "") for item in PurchaseOrderGoods.select().dicts()}


def get_purchase_sku_price_map():
    """
    获取采购单商品的单价map
    获取不含税单价
    :return: {"purchaseId:skuId": finUntaxedPrice}
    """
    return {"{}:{}".format(item.get("purchaseId", ""), item.get("skuId", "")): item.get("finUntaxedPrice", 0)
            for item in PurchaseSku.select().dicts()}


def get_purchase_in_goods(goods_map: dict, base_time=0):
    """
    获取采购入库商品数据
    采购入库的count全部为正
    :goods_map: 商品map
    :return: {
        15978238974 : { // 时间戳
            "2031A00010C161": { // sku
                "price": 23.23,  // 单价
                "count": 3      // 数量，正：入库；负：出库
            }
        }
    }
    """
    sku_map = get_purchase_sku_map()
    sku_price_map = get_purchase_sku_price_map()
    if base_time > 0:
        res = [_ for _ in PurchaseOrder.select(
            PurchaseOrder.submitTime, PurchaseOrder.purchaseId, PurchaseOrderGoodsCount.skuId, PurchaseOrderGoodsCount.wareHouseCount,
        ).where(PurchaseOrder.submitTime < base_time).join(
            PurchaseOrderGoodsCount, on=(PurchaseOrder.warehouseOrderId == PurchaseOrderGoodsCount.wareHouseId)).dicts()]
    else:
        res = [_ for _ in PurchaseOrder.select(
            PurchaseOrder.submitTime, PurchaseOrder.purchaseId, PurchaseOrderGoodsCount.skuId, PurchaseOrderGoodsCount.wareHouseCount,
        ).join(PurchaseOrderGoodsCount, on=(PurchaseOrder.warehouseOrderId == PurchaseOrderGoodsCount.wareHouseId)).dicts()]
    for item in res:
        sku = sku_map.get(item.get("skuId", ""), "")
        count = abs(item.get("wareHouseCount", 0))
        # 单价
        sku_key = "{}:{}".format(item.get("purchaseId", ""), item.get("skuId", ""))
        price = float(sku_price_map.get(sku_key, 0))
        timestamp = Date(item.get("submitTime")).timestamp() if item.get("submitTime") else 0
        sku_item = {
            "price": price,
            "count": count
        }
        if goods_map.get(timestamp, {}):
            origin_sku_item = goods_map.get(timestamp, {}).get(sku, {})
            origin_sku_price = origin_sku_item.get("price", 0)
            origin_sku_count = origin_sku_item.get("count", 0)
            now_sku_price = round((price * count + origin_sku_price * origin_sku_count) / (count + origin_sku_count),
                                  2) if count + origin_sku_count > 0 else 0
            now_sku_item = {
                "price": now_sku_price,
                "count": origin_sku_count + count
            }
            goods_map.get(timestamp, {})[sku] = now_sku_item
        else:
            goods_map.setdefault(timestamp, {})[sku] = sku_item


def get_purchase_refund_goods(goods_map: dict, base_time=0):
    """
    获取采购退货商品数据
    采购退货的count全部为负
    :goods_map: 商品map
    :return: {
        15978238974 : { // 时间戳
            "2031A00010C161": { // sku
                "price": 23.23,  // 单价
                "count": 3      // 数量，正：入库；负：出库
            }
        }
    }
    """
    sku_map = get_purchase_sku_map()
    sku_price_map = get_purchase_sku_price_map()
    if base_time > 0:
        res = [_ for _ in PurchaseRefund.select(
            PurchaseRefund.submitTime, PurchaseRefundGoods.skuId, PurchaseRefundGoods.count, PurchaseRefundGoods.purchaseId).where(
            PurchaseRefund.submitTime < base_time).join(
            PurchaseRefundGoods, on=(PurchaseRefund.returnOrderId == PurchaseRefundGoods.returnOrderId)).dicts()]
    else:
        res = [_ for _ in PurchaseRefund.select(
            PurchaseRefund.submitTime, PurchaseRefundGoods.skuId, PurchaseRefundGoods.count, PurchaseRefundGoods.purchaseId)
            .join(PurchaseRefundGoods, on=(PurchaseRefund.returnOrderId == PurchaseRefundGoods.returnOrderId)).dicts()]
    for item in res:
        sku = sku_map.get(item.get("skuId", ""), "")
        count = abs(item.get("count", 0))
        # 单价
        sku_key = "{}:{}".format(item.get("purchaseId", ""), item.get("skuId", ""))
        price = sku_price_map.get(sku_key, 0)
        timestamp = Date(item.get("submitTime")).timestamp() if item.get("submitTime") else 0
        sku_item = {
            "price": price,
            "count": -count
        }
        if goods_map.get(timestamp, {}):
            goods_map.get(timestamp, {}).setdefault(sku, sku_item)
        else:
            goods_map.setdefault(timestamp, {})[sku] = sku_item
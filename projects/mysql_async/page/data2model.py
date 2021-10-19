from pyspider.helper.date import Date

"""
data 转 model
"""

bill_type_map = {
    5: "销售出库",
    8: "销售退货",
    28: "线下出库",
    6: "采购入库",
    7: "采购退货",
    61: "其他入库",
    62: "其他出库",
    3: "盘盈盘亏",
    41: "调拨入库",
    42: "调拨出库",
}


def whole_inout_order_transfer(body: list):
    """
    全部出入库明细的model 转换
    :param body:
    :return:
    """
    data_list = []
    for item in body:
        transfer_data = {
            "bill_id": item.get("billID") if item.get("billID") else "",
            "bill_code": item.get("billCode") if item.get("billCode") else "",
            "bill_time": Date(item.get("date")).format_es_utc_with_tz() if item.get("date") else 0,
            "bill_date": Date(item.get("time")).format_es_utc_with_tz() if item.get("time") else 0,
            "bill_type": bill_type_map.get(item.get("billType", 0), ""),
            "storage_id": item.get("storageID") if item.get("storageID") else "",
            "storage_name": item.get("storage_name") if item.get("storage_name") else "",
            "spu": item.get("goodsCode") if item.get("goodsCode") else "",
            "sku": item.get("specCode") if item.get("specCode") else "",
            "goods_name": item.get("goodsName") if item.get("goodsName") else "",
            "category_name": item.get("catagoryName") if item.get("catagoryName") else "",
            "goods_color": item.get("specValue1") if item.get("specValue1") else "",
            "goods_size": item.get("specValue2") if item.get("specValue1") else "",
            "remark": item.get("remark") if item.get("remark") else "",
            "in_or_out": item.get("size") if item.get("size") else 0,
            "quantity": item.get("quantity") if item.get("quantity") else 0,
            "cost_price": item.get("costPrice") if item.get("costPrice") else 0,
            "cost_total": item.get("costTotal") if item.get("costTotal") else 0,
            "cost_tax_rate": item.get("costTaxRate") if item.get("costTaxRate") else 0,
            "cost_price_after_tax": item.get("costPriceAfterTax") if item.get("costPriceAfterTax") else 0,
            "cost_total_after_tax": item.get("costTotalAfterTax") if item.get("costTotalAfterTax") else 0,
            "sale_price": item.get("salePrice") if item.get("salePrice") else 0,
            "sale_total": item.get("saleTotal") if item.get("saleTotal") else 0,
            "sale_tax_rate": item.get("saleTaxRate") if item.get("saleTaxRate") else 0,
            "sale_price_after_tax": item.get("salePriceAfterTax") if item.get("salePriceAfterTax") else 0,
            "sale_total_after_tax": item.get("saleTotalAfterTax") if item.get("saleTotalAfterTax") else 0,
            "shop_name": item.get("shopName") if item.get("shopName") else "",
            "tp_tid": item.get("tpTid") if item.get("tpTid") else "",
            "trade_no": item.get("tradeNo") if item.get("tradeNo") else "",
            "custom_nick": item.get("customNick") if item.get("customNick") else "",
            "custom_name": item.get("customName") if item.get("customName") else "",
            "cellphone": item.get("cellphone") if item.get("cellphone") else "",
            "address": item.get("address") if item.get("address") else "",
            "oper_nick": item.get("operNick") if item.get("operNick") else "",
            "express": item.get("express") if item.get("express") else "",
            "express_uid": item.get("expressUid") if item.get("expressUid") else "",
            "pay_way": item.get("payWay") if item.get("payWay") else "",
            "created_at": Date(item.get("sync_time")).format() if item.get("sync_time") else 0,
        }
        data_list.append(transfer_data)
    return data_list

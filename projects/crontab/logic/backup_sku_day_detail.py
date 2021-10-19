from crontab.model.mysql.sku_day_detail import SkuDayDetail
from crontab.repository.shop_stock_repository import get_online_sale_out, get_online_refund, get_offline_sale_out, \
    get_offline_refund, get_purchase_in_goods, get_purchase_refund_goods
from pyspider.helper.date import Date


def backup_sku_day_detail():
    """
    备份每日(昨天)的【商品单位成本】
    备份日期，截止到当日24时静态数据
    备份计算方式：在凌晨跑脚本，计算上一天的商品单位成本；
    warning: 商品的单位成本计算依赖了 based_order_goods、based_refund_order_goods 这两个表(线上销售单和线上退货单),这两个表的数据也是
             脚本跑进去的，因此本备份脚本的执行时间一定要在这两个表的备份脚本执行时间(1:00)之后
    """
    print("开始备份每日(昨天)的【商品单位成本】,now:{}".format(Date.now().format()))
    # ---获取线上的商品销售出库数据---
    print("获取线上的商品销售出库数据")
    goods_map = get_online_sale_out(base_time=Date.now().to_day_start().timestamp())

    # ---获取线上的商品销售退货数据---
    print("获取线上的商品销售退货数据, goods map len:{}".format(len(goods_map)))
    get_online_refund(goods_map, base_time=Date.now().to_day_start().timestamp())

    # ---获取线下的商品销售出库数据---
    print("获取线下的商品销售出库数据, goods map len:{}".format(len(goods_map)))
    get_offline_sale_out(goods_map, base_time=Date.now().to_day_start().timestamp())

    # ---获取线下的商品销售退货数据---
    print("获取线下的商品销售退货数据, goods map len:{}".format(len(goods_map)))
    get_offline_refund(goods_map, base_time=Date.now().to_day_start().timestamp())

    # ---获取采购入库商品数据---
    print("获取采购入库商品数据, goods map len:{}".format(len(goods_map)))
    get_purchase_in_goods(goods_map, base_time=Date.now().to_day_start().timestamp())

    # ---获取采购退货商品数据---
    print("获取采购退货商品数据, goods map len:{}".format(len(goods_map)))
    get_purchase_refund_goods(goods_map, base_time=Date.now().to_day_start().timestamp())

    print("计算备份的每日的【商品单位成本】, goods map len:{}".format(len(goods_map)))
    cost_map = calculate_unit_cost(goods_map)

    # 写入备份数据
    print("写入备份数据")
    write_backup(cost_map)

    print("备份每日(昨天)的【商品单位成本】完成,now:{}".format(Date.now().format()))


def calculate_unit_cost(goods_map: dict) -> dict:
    """
    计算备份的每日的【商品单位成本】
    :param goods_map:
    :return:
    """
    """
    sku_cost_map = {
        sku: {
            "cost": 23.4, # 单位成本
            "num": 4, # 期末数量
        }
    }
    """
    sku_cost_map = {}
    time_list = list(goods_map.keys())
    time_list.sort()
    for time_item in time_list:
        sku_items = goods_map.get(time_item, {})
        for sku, price_item in sku_items.items():
            price = float(price_item.get("price", 0)) if price_item.get("price") else 0
            count = int(price_item.get("count", 0))
            origin_cost = float(sku_cost_map.get(sku, {}).get("cost", 0))
            origin_num = sku_cost_map.get(sku, {}).get("num", 0)
            if count < 0:
                # 出库
                if sku_cost_map.get(sku):
                    # 已有单位成本
                    sku_cost_map.get(sku, {})["num"] = origin_num - abs(count)
                else:
                    # 没有单位成本
                    sku_cost_map.setdefault(sku, {})["num"] = -abs(count)
            else:
                # 入库
                now_cost = (origin_cost * origin_num + abs(count) * price) / (origin_num + abs(count)) \
                    if origin_num + abs(count) > 0 else origin_cost
                if sku_cost_map.get(sku):
                    # 已有单位成本
                    sku_cost_map.get(sku, {})["cost"] = now_cost
                    sku_cost_map.get(sku, {})["num"] = origin_num + abs(count)
                else:
                    # 没有单位成本
                    sku_cost_map.setdefault(sku, {})["cost"] = now_cost
                    sku_cost_map.setdefault(sku, {})["num"] = origin_num + abs(count)

    return sku_cost_map


def write_backup(cost_map: dict):
    """
    写入备份数据
    :param cost_map:
    :return:
    """
    print("开始写入每日商品单位库存的备份数据")
    # 每次100个写入数据库
    insert_count = 0
    insert_data_list = []
    back_up_day = int(Date.now().plus_days(-1).format(full=False).replace("-", ""))
    now = Date.now().format()
    for sku, item in cost_map.items():
        # 单位成本
        cost = item.get("cost", 0)
        data = {
            "back_up_day": back_up_day,
            "sku": sku,
            "cost_price": cost,
            "created_at": now,
        }
        insert_count += 1
        insert_data_list.append(data)
        if insert_count == 100:
            print("insert_count:{}".format(insert_count))
            SkuDayDetail.insert_many(insert_data_list).on_conflict('replace').execute()
            insert_count = 0
            insert_data_list.clear()
    if len(insert_data_list) > 0:
        print("insert_count:{}".format(insert_count))
        SkuDayDetail.insert_many(insert_data_list).on_conflict('replace').execute()
        insert_data_list.clear()
    print("写入每日商品单位库存备份数据完成")


if __name__ == '__main__':
    backup_sku_day_detail()

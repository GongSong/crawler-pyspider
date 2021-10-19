from crontab.model.mysql.shop_sku_day_stock import ShopSkuDayStock
from crontab.repository.shop_stock_repository import get_warehouse_shop_by_types, get_shop_types_by_ids, \
    get_product_total, get_inout_order_stock, get_inout_order_goods_map
from pyspider.helper.date import Date


def backup_daily_shop_stock(day=0):
    """
    备份每日(昨天)的店铺商品库存
    备份日期，截止到当日24时静态数据
    备份计算方式：在凌晨跑脚本，计算上一天的库存；
    当日24时静态数据 = 用获取到的实时库存 - 次日零点之后产生的出入库存
    :day: 倒推某一天的库存备份, 默认0，获取昨天一整天的库存备份
    """
    backup_date = Date.now().plus_days(-day-1).format(full=False)
    print("开始备份日期:{}的店铺商品库存,now:{}".format(backup_date, Date.now().format()))
    # 备份除了总仓的类型的仓库：门店仓: 1，地方仓:3,品牌仓: 4;
    shop_types = [1, 3, 4]
    warehouse_ids, warehouse_shop_map = get_warehouse_shop_by_types(shop_types)
    # 获取仓库对应门店的类型：0:直营, 1:加盟, 2:联营
    shop_type_map = get_shop_types_by_ids(list(warehouse_shop_map.values()))
    # 获取所有仓的实时商品库存
    print("获取所有仓的实时商品库存")
    stock_map = get_product_total(warehouse_ids)
    # 获取前一天24点之后产生的商品出入库存数量
    print("获取日期：{} 24点之后产生的商品出入库存数量".format(backup_date))
    after_inout_orders = get_inout_order_stock(Date.now().plus_days(-day).to_day_start().timestamp())
    order_goods_sku_map = get_inout_order_goods_map(list(after_inout_orders.keys()))
    # 计算备份的每日店铺商品库存
    print("计算备份的每日店铺商品库存")
    calculate_backup_stock(stock_map, after_inout_orders, order_goods_sku_map)
    # 写入备份数据
    write_backup(stock_map, warehouse_shop_map, shop_type_map, day)
    print("备份日期:{} 的店铺商品库存完成,now:{}".format(backup_date, Date.now().format()))


def calculate_backup_stock(stock_map: dict, after_inout_orders: dict, order_goods_sku_map: dict) -> dict:
    """
    计算备份的每日店铺商品库存
    24点产生的出入库，如果是出库，则加回来；如果是入库，则减掉
    :param stock_map: 所有仓的实时商品库存
    :param after_inout_orders: 前一天24点之后产生的商品出入库
    :param order_goods_sku_map: 前一天24点之后产生的商品出入库对应的商品变动详情
    :return:
    """
    for inout_order_id, warehouse_id in after_inout_orders.items():
        changed_skus = list(order_goods_sku_map.get(inout_order_id, {}).keys())
        for changed_sku in changed_skus:
            if stock_map.get(warehouse_id, {}).get(changed_sku):
                # 在实际库存中如果有24点之后产生的商品出入库，则更新库存
                origin_actual_stock = stock_map.get(warehouse_id, {}).get(changed_sku, {}).get("actual_stock", 0)
                origin_available_stock = stock_map.get(warehouse_id, {}).get(changed_sku, {}).get("available_stock", 0)
                stock_map.get(warehouse_id, {}).get(changed_sku, {})["actual_stock"] = origin_actual_stock - \
                                                       order_goods_sku_map.get(inout_order_id, {}).get(changed_sku, 0)
                stock_map.get(warehouse_id, {}).get(changed_sku, {})["available_stock"] = origin_available_stock - \
                                                       order_goods_sku_map.get(inout_order_id, {}).get(changed_sku, 0)
            else:
                # 有出入库的商品，但在实际库存中的sku不存在(库存为0的被过滤了),需要把出入库的数量反推到备份库存
                stock_map.setdefault(warehouse_id, {}).setdefault(changed_sku, {})["actual_stock"] = 0 - \
                                                       order_goods_sku_map.get(inout_order_id, {}).get(changed_sku, 0)
                stock_map.setdefault(warehouse_id, {}).setdefault(changed_sku, {})["available_stock"] = 0 - \
                                                       order_goods_sku_map.get(inout_order_id, {}).get(changed_sku, 0)


def write_backup(stock_map: dict, warehouse_shop_map: dict, shop_type_map: dict, day=0):
    """
    写入每日店铺商品备份数据
    :param stock_map: 每日的店铺商品备份数据
    :param warehouse_shop_map: 仓库ID和店铺ID的映射关系
    :param shop_type_map: 店铺ID和店铺类型的映射关系
    :param day: 倒推某一天的库存备份, 默认0，获取昨天一整天的库存备份
    :return:
    """
    backup_date = Date.now().plus_days(-day-1).format(full=False)
    print("开始写入日期:{}的店铺商品备份数据".format(backup_date))
    # 每次100个写入数据库
    insert_count = 0
    insert_data_list = []
    back_up_day = int(Date.now().plus_days(-day-1).format(full=False).replace("-", ""))
    # 每次100个写入数据库
    now = Date.now().format()
    for warehouse_id, sku_items in stock_map.items():
        for sku, stock_item in sku_items.items():
            actual_stock = stock_item.get("actual_stock", 0)
            underway_stock = stock_item.get("underway_stock", 0)
            lock_stock = stock_item.get("lock_stock", 0)
            available_stock = stock_item.get("available_stock", 0)
            if actual_stock == 0 and underway_stock == 0 and lock_stock == 0 and available_stock == 0:
                continue
            data = {
                "back_up_day": back_up_day,
                "sku": sku,
                "warehouse_id": warehouse_id,
                "shop_id": warehouse_shop_map.get(warehouse_id, 0),
                "shop_type": shop_type_map.get(warehouse_shop_map.get(warehouse_id, 0), 0),
                "actual_stock": actual_stock,
                "underway_stock": underway_stock,
                "lock_stock": lock_stock,
                "available_stock": available_stock,
                "created_at": now,
            }
            insert_count += 1
            insert_data_list.append(data)
            if insert_count == 100:
                print("insert_count:{}".format(insert_count))
                ShopSkuDayStock.insert_many(insert_data_list).on_conflict('replace').execute()
                insert_count = 0
                insert_data_list.clear()
    if len(insert_data_list) > 0:
        print("insert_count:{}".format(insert_count))
        ShopSkuDayStock.insert_many(insert_data_list).on_conflict('replace').execute()
        insert_data_list.clear()
    print("写入日期:{}店铺商品备份数据完成".format(backup_date))


if __name__ == '__main__':
    for day in range(30, 150):
        backup_daily_shop_stock(day)

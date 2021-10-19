from crontab.model.mysql.online_sku_day_stock import OnlineSkuDayStock
from crontab.repository.shop_stock_repository import get_online_product_total, get_online_inout_order_stock, \
    get_online_inout_order_goods_map
from hupun_slow_crawl.model.es.store_house import StoreHouse
from pyspider.helper.date import Date


def backup_daily_online_stock():
    """
    备份每日(昨天)的线上商品库存
    备份日期，截止到当日24时静态数据
    备份计算方式：在凌晨跑脚本，计算上一天的库存；
    当日24时静态数据 = 用获取到的实时库存 - 次日零点之后产生的出入库存
    """
    print("开始备份每日(昨天)的线上商品库存,now:{}".format(Date.now().format()))
    # 所有的仓库ID
    storage_ids_map = StoreHouse().get_storage_ids_map()
    # 获取线上仓库的实时商品库存
    print('获取线上仓库的实时商品库存')
    stock_map = get_online_product_total(list(storage_ids_map.keys()))
    # 获取前一天24点之后产生的商品出入库存数量
    print("获取前一天24点之后产生的商品出入库存数量")
    after_inout_orders = get_online_inout_order_stock(Date.now().to_day_start().format())
    order_goods_sku_map = get_online_inout_order_goods_map(list(after_inout_orders.keys()))
    # 计算备份的每日线上店铺商品库存
    print("计算备份的每日线上店铺商品库存")
    calculate_backup_stock(stock_map, after_inout_orders, order_goods_sku_map)
    # 写入备份数据
    write_backup(stock_map, storage_ids_map)
    print("备份每日(昨天)的线上商品库存完成,now:{}".format(Date.now().format()))


def calculate_backup_stock(stock_map: dict, after_inout_orders: dict, order_goods_sku_map: dict) -> dict:
    """
    计算备份的每日线上店铺商品库存
    24点产生的出入库，如果是出库，则加回来；如果是入库，则减掉
    :param stock_map: 所有门店仓的实时商品库存
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
                                                      order_goods_sku_map.get(inout_order_id, {}).get(changed_sku)
                stock_map.get(warehouse_id, {}).get(changed_sku, {})["available_stock"] = origin_available_stock - \
                                                      order_goods_sku_map.get(inout_order_id, {}).get(changed_sku)


def write_backup(stock_map: dict, storage_ids_map: dict):
    """
    写入每日线上店铺商品备份数据
    :param stock_map: 每日的线上仓库商品备份数据
    :param storage_ids_map: 线上仓库ID和名字的映射
    :return:
    """
    print("开始写入每日线上店铺商品备份数据")
    # 每次100个写入数据库
    insert_count = 0
    insert_data_list = []
    back_up_day = int(Date.now().plus_days(-1).format(full=False).replace("-", ""))
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
                "storage_id": warehouse_id,
                "storage_name": storage_ids_map.get(warehouse_id, ""),
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
                OnlineSkuDayStock.insert_many(insert_data_list).on_conflict('replace').execute()
                insert_count = 0
                insert_data_list.clear()
    if len(insert_data_list) > 0:
        print("insert_count:{}".format(insert_count))
        OnlineSkuDayStock.insert_many(insert_data_list).on_conflict('replace').execute()
        insert_data_list.clear()
    print("写入每日线上店铺商品备份数据完成")


if __name__ == '__main__':
    backup_daily_online_stock()

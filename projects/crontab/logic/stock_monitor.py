"""
仓库服务的库存监控
"""
from alarm.page.ding_talk import DingTalk
from crontab.config import prod_filter_warehouse_ids, ROBOT_TOKEN
from crontab.model.mysql.order_goods import OrderGoods
from crontab.model.mysql.order_info import OrderInfo
from crontab.model.mysql.product import Product


class StockMonitor:

    def __init__(self):
        pass

    def run(self):
        # 基准库存
        base_goods_map = self.get_product_total()

        # 出入库明细计算出来的库存
        # 出入库map, key: orderId, value: warehouseId
        order_map = self.get_inout_order_map()
        # 出入库商品的map, key:sku:warehouse, value: count
        order_goods_map = self.get_inout_order_goods_map(order_map)
        # 对比出有库存差异的sku
        diff_sku_map = {}
        for sku_key, stock in base_goods_map.items():
            if sku_key in order_goods_map:
                order_goods_count = order_goods_map.get(sku_key)
                if order_goods_count != stock:
                    diff_sku_map.setdefault(sku_key, stock - order_goods_count)
            else:
                if stock != 0:
                    diff_sku_map.setdefault(sku_key, stock)

        print("有差异的库存: {}".format(diff_sku_map))
        err_msg = ""
        for item, count in diff_sku_map.items():
            sku, warehouse_id = item.split(":")
            err_msg += "sku: {} 在仓库: {} 相差的库存为: {}".format(sku, warehouse_id, count) + "\n"
        if err_msg:
            DingTalk(ROBOT_TOKEN, "库存监控报警", err_msg).enqueue()

    def get_product_total(self) -> dict:
        """
        获取所有的商品库存
        :rtype: object
        """
        goods_map = {}
        res = [_ for _ in Product.select().where(Product.warehouse_id << prod_filter_warehouse_ids).dicts()]
        for item in res:
            sku = item.get("sku", "")
            warehouse_id = item.get("warehouse_id", 0)
            key = "{}:{}".format(sku, warehouse_id)
            goods_map.setdefault(key, item.get("actual_stock", 0))
        return goods_map

    def get_inout_order_map(self) -> dict:
        """
        出入库map
        :rtype: object
        """
        order_map = {}
        res = [_ for _ in OrderInfo.select().where(OrderInfo.warehouse_id << prod_filter_warehouse_ids).dicts()]
        for item in res:
            order_id = item.get("code", "")
            warehouse_id = item.get("warehouse_id", 0)
            order_map.setdefault(order_id, warehouse_id)
        return order_map

    def get_inout_order_goods_map(self, order_map: dict) -> dict:
        """
        出入库商品的map
        :return:
        """
        order_goods_sku_map = {}
        res = [_ for _ in OrderGoods.select().dicts()]
        for item in res:
            sku = item.get("sku_id", "")
            order_id = item.get("order_id", "")
            count = item.get("count", 0)
            key = "{}:{}".format(sku, order_map.get(order_id, 0))
            if key in order_goods_sku_map:
                if "CK" in order_id:
                    order_goods_sku_map[key] = order_goods_sku_map.get(key) - count
                else:
                    order_goods_sku_map[key] = order_goods_sku_map.get(key) + count
            else:
                if "CK" in order_id:
                    order_goods_sku_map[key] = -count
                else:
                    order_goods_sku_map[key] = count
        return order_goods_sku_map


if __name__ == '__main__':
    StockMonitor().run()

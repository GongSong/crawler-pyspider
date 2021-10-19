import gevent.monkey

from crontab.logic.backup_daily_online_stock import backup_daily_online_stock
from crontab.logic.backup_daily_shop_stock import backup_daily_shop_stock
from crontab.logic.backup_sku_day_detail import backup_sku_day_detail

gevent.monkey.patch_ssl()

import fire
from crontab.logic.stock_monitor import StockMonitor
from pyspider.helper.date import Date


class Cron:
    def monitor_stock(self):
        """
        对比商品的实际库存和出入库单据的库存差异
        :return:
        """
        print('开始对比商品的实际库存和出入库单据的库存差异, now:{}'.format(Date.now().format()))
        StockMonitor().run()
        print('对比商品的实际库存和出入库单据的库存差异完成')

    def backup_daily_shop_stock(self, day=0, his=False):
        """
        备份每日的线下店铺库存
        :param day: 备份的日期，默认是当天(当天备份的是昨天一整天的库存)
        :param his: 是否备份历史的线下店铺库存
        :return:
        """
        print("开始备份每日的线下店铺库存,day:{},his:{}, now:{}".format(day, his, Date.now().format()))
        if his:
            for day_item in range(day):
                backup_daily_shop_stock(day_item)
        else:
            backup_daily_shop_stock()
        print("备份每日的线下店铺库存完成, now:{}".format(Date.now().format()))

    def backup_daily_online_stock(self):
        """
        备份每日的线上店铺库存
        :return:
        """
        print("开始备份每日的线上店铺库存, now:{}".format(Date.now().format()))
        backup_daily_online_stock()
        print("备份每日的线上店铺库存完成, now:{}".format(Date.now().format()))

    def backup_sku_day_detail(self):
        """
        备份每日(昨天)的【商品单位成本】
        :return:
        """
        print("开始备份每日(昨天)的【商品单位成本】, now:{}".format(Date.now().format()))
        backup_sku_day_detail()
        print("备份每日(昨天)的【商品单位成本】完成, now:{}".format(Date.now().format()))


if __name__ == '__main__':
    fire.Fire(Cron)

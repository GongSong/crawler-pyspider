import fire
import time

from alarm.helper import Helper
from alarm.page.ding_talk import DingTalk
from hupun_slow_crawl.model.es.store_house import StoreHouse
from hupun.model.es.goods_sku import GoodsSku as GoodsSkuEs
from hupun_api.model.es.goods_inventory import GoodsInventoryApi
from hupun_api.model.mysql.sku_inventory import SkuInventory
from hupun_inventory.config import MAX_ALL_INVENTORY, ROBOT_TOKEN
from hupun_inventory.model.result import HupunInventoryTask
from hupun_inventory.page.goods_inventory import GoodsInventory
from hupun_inventory.page.goods_inventory_sku import GoodsInventorySku
from pyspider.helper.date import Date
from pyspider.helper.es_query_builder import EsQueryBuilder
from pyspider.helper.utils import generator_list


class Cron:
    def inventory_sku(self, hour=1, is_all=False):
        """
        获取 商品库存sku 的数据
        :param hour: 抓近几小时的数据
        :param is_all: 是否全量抓取数据
        :return:
        """
        # 所有的仓库ID
        storage_ids = StoreHouse().get_storage_ids()
        # 指定范围内的库存API的数据
        sku_code_set = set()
        if not is_all:
            sku_codes = GoodsInventoryApi().scroll(
                EsQueryBuilder().range_gte('sync_time', Date.now().plus_hours(-hour).millisecond(), None).source(
                    ['sku_code']))
            for _code in sku_codes:
                for _c in _code:
                    sku_code_set.add(_c['sku_code'])
            # 所有的商品sku数据
            if not sku_code_set:
                print("未获取到近:{}个小时的商品库存数据".format(hour))
                return
            data = GoodsSkuEs().scroll(EsQueryBuilder().terms('goodsCode.keyword', list(sku_code_set)).range_gte(
                'sync_time', Date.now().plus_days(-1).millisecond(), None).source(['goodsUid', 'specUid', 'goodsCode']))
        else:
            data = GoodsSkuEs().scroll(EsQueryBuilder().source(['goodsUid', 'specUid', 'goodsCode']))
        middle_set = set()
        for _d in data:
            for _i in _d:
                item_id = _i['goodsUid']
                sku_id = _i['specUid']
                spec_code = _i['goodsCode']
                middle_set.add(':'.join([item_id, sku_id, spec_code]))
        print("本次更新商品库存的sku数量:{}".format(len(middle_set)))
        gen_list = generator_list(middle_set, 300)
        for _ge in gen_list:
            # 延迟入队的时间
            count = HupunInventoryTask().find({'status': 1}).count()
            print('queue status:1 count: {}'.format(count))
            while count >= MAX_ALL_INVENTORY:
                time.sleep(int(count) / 6)
                count = HupunInventoryTask().find({'status': 1}).count()
            for _m in _ge:
                item_id, sku_id, spec_code = _m.split(':')
                if is_all:
                    GoodsInventorySku(storage_ids, item_id, sku_id, spec_code).set_priority(
                        GoodsInventorySku.CONST_PRIORITY_SECOND).enqueue()
                else:
                    GoodsInventorySku(storage_ids, item_id, sku_id, spec_code).set_priority(
                        GoodsInventorySku.CONST_PRIORITY_BUNDLED).enqueue()

    def goods_inventory(self):
        """
        商品库存 的数据
        :return:
        """
        storage_ids = StoreHouse().get_storage_ids()
        GoodsInventory(storage_ids, True).set_priority(GoodsInventory.CONST_PRIORITY_FIRST).enqueue()

    def inventory_checker(self):
        """
        商品库存sku 的检查预警脚本
        取消数据库和万里牛的库存量数量对比，改为直接检查sku库存的最后更新时间，因为库存API的更新非常及时
        :return:
        """
        # 取消数据库和万里牛的库存量数量对比
        # storage_ids = StoreHouse().get_storage_ids()
        # GoodsInventoryChecker(storage_ids).set_priority(GoodsInventoryChecker.CONST_PRIORITY_BUNDLED).enqueue()
        data = SkuInventory.select().order_by(SkuInventory.update_time.desc()).limit(1).dicts()
        for _d in data:
            update_time = _d.get('update_time', 0)
            # 2小时以上还没更新，则报警
            now = Date.now().plus_hours(-2)
            print('update_time', update_time)
            if update_time < now and Helper.in_project_env():
                print('有问题')
                title = '万里牛sku库存异常报警'
                text = '万里牛sku库存的最后更新时间:{}, 超过2小时未更新, 报警'.format(Date(update_time).format())
                DingTalk(ROBOT_TOKEN, title, text).enqueue()
            else:
                print('没有问题')

    def clear(self):
        """
        清除过期的库存数据
        :return:
        """
        pass
        # GoodsInvenEs().clear_invalid(Date.now(), 24 * 3600)
        # GoodsInvenSkuEs().clear_invalid(Date.now(), 24 * 3600)


if __name__ == '__main__':
    fire.Fire(Cron)

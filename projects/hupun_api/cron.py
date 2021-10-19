import time

import gevent.monkey
gevent.monkey.patch_ssl()
import json
import traceback
import fire

from hupun_api.model.es.store_house import StoreHouse
from hupun_api.model.mysql.sku_inventory import SkuInventory
from hupun_api.page.inventory import InventoryApi
from hupun_api.page.order import OrderApi
from pyspider.helper.date import Date


class Cron:
    def fetch_inventory_api(self, hour=1):
        """
        获取库存API的数据，写入es
        :param hour:
        :return:
        """
        page_no = 1
        page_size = 200
        modify_time = Date.now().plus_hours(-hour).millisecond()
        storage = StoreHouse().get_storage()
        for _s in storage:
            # 万里牛的接口访问频率有限制，每分钟100次,爬虫入队时降低频率
            time.sleep(1)
            InventoryApi(to_next_page=True) \
                .set_param('storage', _s) \
                .set_param('modify_time', modify_time) \
                .set_page(page_no) \
                .set_page_size(page_size).enqueue()

    def crawl_inventory_api_to_mysql(self, modify_hour=1, start_page=1):
        """
        获取库存API的数据，写入mysql
        :param modify_hour: 抓取近多少小时的库存数据
        :param start_page: 初始页码，用来指定从哪一页开始抓取
        :return:
        """
        try:
            print('开始获取库存API的数据并写入mysql')
            # if not SkuInventory.table_exists():
            #     SkuInventory.create_table()
            # return
            # 获取库存数据
            sync_timestamp = Date.now().datetime
            storage = StoreHouse().get_storage()
            for _s in storage:
                print('获取仓库:{}的近:{}小时的库存数据,now:{}'.format(_s, float(modify_hour), Date.now().format()))
                page_no = int(start_page)
                page_size = 100
                while True:
                    try:
                        print('获取第:{}页的库存数据'.format(page_no))
                        modify_time = Date.now().plus_hours(-float(modify_hour)).millisecond()
                        result = InventoryApi() \
                            .set_param('storage', _s) \
                            .set_param('modify_time', modify_time) \
                            .set_param('page_no', page_no) \
                            .set_param('page_size', page_size).get_result()
                        storage_code = result['post_data']['storage']
                        data_list = result['result']
                        data = json.loads(data_list)['data']
                        if not data:
                            print('未获取到第:{}页的库存sku数据，本次请求结束.'.format(page_no))
                            break
                        for _d in data:
                            goods_code = _d['goods_code']
                            lock_size = int(_d['lock_size'])
                            quantity = int(_d['quantity'])
                            sku_code = _d['sku_code']
                            underway = int(_d['underway'])
                            update_time = sync_timestamp
                            SkuInventory.insert(
                                goods_code=goods_code,
                                lock_size=lock_size,
                                quantity=quantity,
                                sku_code=sku_code,
                                skc_code=sku_code[:-2],
                                underway=underway,
                                update_time=update_time,
                                storage_code=storage_code,
                            ).on_conflict('replace').execute()
                            print('保存数据:sku_code:{},storage_code:{}成功'.format(sku_code, storage_code))
                        page_no += 1
                    except Exception as e:
                        print('写入到mysql的数据失败: {}, 失败页码数:{}, 仓库: {}'.format(e, page_no, _s))
                        break
        except Exception as e:
            print('抓取库存API的数据保存到mysql的脚本异常: {}'.format(e))
            print(traceback.format_exc())

    def order_checker(self):
        """
        检测订单数据是否正常抓取，监控数据并报警
        :return:
        """
        pass

    def _crawl_order_api(self, modify_hour=1, start_page=1):
        """
        获取订单API的数据;
        暂时不使用cron来启动订单数据的抓取写入mysql;
        使用handler的方式来启动订单数据抓取, 写入es;
        :param modify_hour: 抓取近多少小时的数据
        :param start_page: 初始页码，用来指定从哪一页开始抓取
        :return:
        """
        print('开始获取订单API的数据')
        page_size = 20

        page_no = int(start_page)
        while True:
            try:
                print('获取第:{}页的订单数据'.format(page_no))
                modify_time = Date.now().plus_hours(-modify_hour).millisecond()
                resp = OrderApi() \
                    .set_param('page', page_no) \
                    .set_param('limit', page_size) \
                    .set_param('modify_time', modify_time) \
                    .get_result()
                print('resp', resp)
                resp_js = json.loads(resp)
                code = int(resp_js.get('code'))
                data = resp_js.get('data')
                if code != 0 or not data:
                    print('未获取到第:{}页的订单数据，本次请求结束.'.format(page_no))
                    break
                page_no += 1
            except Exception as e:
                print('写入到mysql的数据失败: {}, 失败页码数:{}'.format(e, page_no))
                print(traceback.format_exc())


if __name__ == '__main__':
    fire.Fire(Cron)

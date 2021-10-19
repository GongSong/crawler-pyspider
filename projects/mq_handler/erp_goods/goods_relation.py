import traceback

from alarm.page.ding_talk import DingTalk
from hupun_operator.page.goods_info.update_goods_relation import UpdateGoodsRe
from hupun_slow_crawl.model.es.shop_data import ShopData
from mq_handler.base import Base
from pyspider.core.model.storage import StorageRedis
from pyspider.helper.crawler_utils import CrawlerHelper
from pyspider.helper.date import Date


class GoodsRelation(Base):
    """
    更新erp的商品对应关系
    """
    ROBOT_TOKEN = '58c52b735767dfea3be10898320d4cf11af562b4b6ac6a2ea94be7de722cfbf9'
    # 线上环境
    REDIS_HOST = '10.0.5.5'
    REDIS_PORT = 5304
    REDIS_DB = 0
    # 测试环境
    # REDIS_HOST = '10.0.5.5'
    # REDIS_PORT = 5303
    # REDIS_DB = 8
    # key 对应的值: 2，操作中；1，操作完成；0，操作失败
    REDIS_KEY = 'shelf.updateGoodsRelations'

    def execute(self):
        print('开始更新erp的商品对应关系')
        self.print_basic_info()

        try:
            self.entry()
        except Exception as e:
            err_msg = '更新erp的商品对应关系发生未知异常:{};'.format(e)
            print(err_msg)
            print('------')
            print(traceback.format_exc())
            print('------')
            # 发送失败的消息
            if CrawlerHelper.in_project_env():
                title = '万里牛操作:更新erp的商品对应关系发生未知异常'
                ding_msg = err_msg
                DingTalk(self.ROBOT_TOKEN, title, ding_msg).enqueue()

    def entry(self):
        """
        商品对应关系的入口
        :return:
        """
        try:
            print('同步商品对应关系的入口')
            # 设置同步商品对应关系的redis的状态,同步中
            StorageRedis(host=self.REDIS_HOST, port=self.REDIS_PORT, db=self.REDIS_DB).set(self.REDIS_KEY, 2)

            if not isinstance(self._data.get('shop_name'), list):
                assert False, '更新erp的商品对应关系传入的店铺名不是list'
            for name in self._data.get('shop_name'):
                shop_uid = ShopData().find_shop_by_name(name)['shop_uid']
                re_obj = UpdateGoodsRe(shop_uid, name) \
                    .set_start_time(Date.now().plus_days(-30)) \
                    .use_cookie_pool()
                re_status, re_result = CrawlerHelper.get_sync_result(re_obj)
                if re_status == 1:
                    assert False, '爬虫同步商品对应关系的请求失败:{}'.format(re_result)
                if not re_result.get('response', {}).get('data'):
                    assert False, '爬虫同步商品对应关系的请求响应错误:{}'.format(re_result)
                print('response', re_result.get('response'))
            # 设置同步商品对应关系的redis的状态,完成
            StorageRedis(host=self.REDIS_HOST, port=self.REDIS_PORT, db=self.REDIS_DB).set(self.REDIS_KEY, 1)
        except Exception as e:
            err_msg = '更新erp的商品对应关系error:{};'.format(e)
            print(err_msg)
            print(traceback.format_exc())
            # 设置同步商品对应关系的redis的状态,失败
            StorageRedis(host=self.REDIS_HOST, port=self.REDIS_PORT, db=self.REDIS_DB).set(self.REDIS_KEY, 0)

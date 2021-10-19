from pyspider.helper.date import Date
from pyspider.libs.base_crawl import *
from pyspider.helper.logging import processor_logger
from monitor_shop_goods.model.shop import Shop
from alarm.helper import Helper
from monitor_shop_goods.config import USER_AGENT, TOKEN


class ShelfTaoBao(BaseCrawl):
    # 淘宝渠道商品上下架通知
    URL = 'https://item.taobao.com/item.htm?id={}'
    headers = {'User-Agent': USER_AGENT}

    def __init__(self, goods_id):
        super(ShelfTaoBao, self).__init__()
        self.__goods_id = goods_id
        self.__channel = 'taobao'
        self.__goods_url = self.URL.format(goods_id)

    def crawl_builder(self):
        return CrawlBuilder() \
            .set_url(self.__goods_url) \
            .set_headers(self.headers) \
            .set_kwargs_kv('validate_cert', False) \
            .schedule_age(1) \
            .set_task_id(md5string(self.__channel + self.__goods_id))

    def parse_response(self, response, task):
        doc = response.doc
        processor_logger.info('goods_url: {}'.format(self.__goods_url))
        processor_logger.info('goods_id: {}'.format(self.__goods_id))

        # 判断商品是否下架
        off_shelf_soup2 = doc('p.tb-hint')
        processor_logger.info('off_shelf_soup2: {}'.format(off_shelf_soup2))
        if off_shelf_soup2:
            off_shelf = True
            processor_logger.info('already offshelf')
        else:
            off_shelf = False
        off_shelf_soup1 = doc('div.error-notice-hd')
        processor_logger.info('off_shelf_soup1: {}'.format(off_shelf_soup1))
        if off_shelf_soup1:
            be_deleted = True
            processor_logger.info('商品: {}已被删除'.format(self.__goods_url))
        else:
            be_deleted = False
        if off_shelf or be_deleted:
            off_shelf = True
            processor_logger.info(
                '商品: {}already offshelf'.format(self.__goods_url))

        goods = Shop().find_one({'goods_id': self.__goods_id})
        if goods is None:
            processor_logger.error(
                '商品: {}未入库，请检查这个异常商品.'.format(self.__goods_id))
        else:
            processor_logger.info('存在商品：{}'.format(self.__goods_id))
            goods_status = goods.get('status')
            update_time = Date.now().format()
            if goods_status != off_shelf:
                title = "淘宝渠道"
                if off_shelf == True:
                    trace = '淘宝商品：{}下架了'.format(self.__goods_url)
                    processor_logger.info(trace)
                else:
                    trace = '淘宝商品：{}上架了'.format(self.__goods_url)
                    processor_logger.info(trace)
                Helper.send_to_ding_talk(TOKEN, title, trace)
                Shop().update(
                    {
                        'goods_id': self.__goods_id,
                    },
                    {
                        'status': off_shelf,
                        'update_time': update_time,
                    }
                )
                return {
                    'status': off_shelf
                }


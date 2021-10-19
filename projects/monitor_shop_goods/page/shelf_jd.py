from alarm.helper import Helper
from pyspider.helper.date import Date
from pyspider.libs.base_crawl import *
from pyspider.helper.logging import processor_logger
from monitor_shop_goods.model.shop import Shop
from monitor_shop_goods.config import USER_AGENT, TOKEN


class ShelfJD(BaseCrawl):
    # 京东渠道商品上下架通知
    URL = 'https://item.jd.com/{}.html'
    headers = {'User-Agent': USER_AGENT}

    def __init__(self, goods_id):
        super(ShelfJD, self).__init__()
        self.__goods_id = goods_id
        self.__channel = 'jd'
        self.__goods_url = self.URL.format(goods_id)

    def crawl_builder(self):
        return CrawlBuilder() \
            .set_url(self.__goods_url) \
            .set_headers(self.headers) \
            .set_kwargs_kv('validate_cert', False) \
            .set_task_id(md5string(self.__channel + self.__goods_id))

    def parse_response(self, response, task):
        doc = response.doc
        processor_logger.info('jingdong goods_url: {}'.format(self.__goods_url))
        processor_logger.info('jingdong goods_id: {}'.format(self.__goods_id))

        # 判断商品是否下架
        off_shelf_soup = doc('div.itemover-tip')
        if off_shelf_soup:
            off_shelf = True
            processor_logger.info(
                "京东商品: {}already offshelf".format(self.__goods_id))
        else:
            off_shelf = False

        goods = Shop().find_one({'goods_id': self.__goods_id})
        if goods is None:
            processor_logger.error(
                '京东商品: {}未入库，请检查这个异常商品.'.format(self.__goods_id))
        else:
            processor_logger.info('存在京东商品: {}'.format(self.__goods_id))
            goods_status = goods.get('status')
            update_time = Date.now().format()
            if goods_status != off_shelf:
                title = "京东渠道"
                if off_shelf == True:
                    trace = '京东商品: {} 下架了'.format(self.__goods_url)
                    processor_logger.info(trace)
                else:
                    trace = '京东商品: {} 上架了'.format(self.__goods_url)
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

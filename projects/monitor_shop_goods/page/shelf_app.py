from alarm.helper import Helper
from pyspider.helper.date import Date
from pyspider.libs.base_crawl import *
from pyspider.helper.logging import processor_logger
from monitor_shop_goods.model.shop import Shop
from monitor_shop_goods.config import USER_AGENT, TOKEN

import json


class ShelfApp(BaseCrawl):
    # App渠道商品上下架通知
    URL = 'https://ichuanyi.com/m.php?method=goods.getInfo&goodsId={}&isFromApp=1'
    headers = {'User-Agent': USER_AGENT}

    def __init__(self, goods_id):
        super(ShelfApp, self).__init__()
        self.__goods_id = goods_id
        self.__channel = 'app'
        self.__goods_url = self.URL.format(goods_id)

    def crawl_builder(self):
        return CrawlBuilder() \
            .set_url(self.__goods_url) \
            .set_headers(self.headers) \
            .set_kwargs_kv('validate_cert', False) \
            .set_task_id(md5string(self.__channel + self.__goods_id))

    def parse_response(self, response, task):
        doc = response.text
        processor_logger.info('chuanyi goods_url: {}'.format(self.__goods_url))
        processor_logger.info('chuanyi goods_id: {}'.format(self.__goods_id))

        # 判断商品是否下架
        status = json.loads(doc)['data'].get('soldOutBtnContent', '')
        if status:
            off_shelf = True
            processor_logger.info(
                "dresshelper goods: {}already offshelf".format(self.__goods_id))
        else:
            off_shelf = False

        goods = Shop().find_one({'goods_id': self.__goods_id})
        if goods is None:
            processor_logger.error(
                'dresshelper goods: {}未入库，请检查这个异常商品.'.format(self.__goods_id))
        else:
            processor_logger.info(
                '存在dresshelper goods: {}'.format(self.__goods_id))
            goods_status = goods.get('status')
            update_time = Date.now().format()
            if goods_status != off_shelf:
                title = "App渠道"
                if off_shelf == True:
                    msg_url = 'https://icy.design/icy/goodsDetail?goodsId={}'.format(
                        self.__goods_id)
                    trace = 'dresshelper goods: {} 下架了'.format(msg_url)
                    processor_logger.info(trace)
                else:
                    msg_url = 'https://icy.design/icy/goodsDetail?goodsId={}'.format(
                        self.__goods_id)
                    trace = 'dresshelper goods: {} 上架了'.format(msg_url)
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

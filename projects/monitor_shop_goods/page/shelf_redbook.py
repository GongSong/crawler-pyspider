from alarm.helper import Helper
from pyspider.helper.date import Date
from pyspider.libs.base_crawl import *
from pyspider.helper.logging import processor_logger
from monitor_shop_goods.model.shop import Shop
from monitor_shop_goods.config import USER_AGENT, TOKEN

import json


class ShelfRedBook(BaseCrawl):
    # 小红书渠道商品上下架通知
    URL = 'https://www.xiaohongshu.com/api/store/jpd/{}'
    headers = {'User-Agent': USER_AGENT}

    def __init__(self, goods_id):
        super(ShelfRedBook, self).__init__()
        self.__goods_id = goods_id
        self.__channel = 'redbook'
        self.__goods_url = self.URL.format(goods_id)

    def crawl_builder(self):
        return CrawlBuilder() \
            .set_url(self.__goods_url) \
            .set_headers(self.headers) \
            .set_kwargs_kv('validate_cert', False) \
            .set_task_id(md5string(self.__channel + self.__goods_id))

    def parse_response(self, response, task):
        doc = response.text
        processor_logger.info(
            'xiaohongshu goods_url: {}'.format(self.__goods_url))
        processor_logger.info(
            'xiaohongshu goods_id: {}'.format(self.__goods_id))

        # 判断商品是否下架
        try:
            status = int(json.loads(doc)['data']['cart'].get('count', ''))
        except Exception as e:
            status = 0
            processor_logger.info("error msg: {}".format(e))
        if status == 0:
            off_shelf = True
            processor_logger.info(
                "小红书商品: {}already offshelf".format(self.__goods_id))
        else:
            off_shelf = False

        goods = Shop().find_one({'goods_id': self.__goods_id})
        if goods is None:
            processor_logger.error(
                '小红书商品: {}未入库，请检查这个异常商品.'.format(self.__goods_id))
        else:
            processor_logger.info('存在小红书商品: {}'.format(self.__goods_id))
            goods_status = goods.get('status')
            update_time = Date.now().format()
            if goods_status != off_shelf:
                title = "小红书渠道"
                if off_shelf == True:
                    msg_url = 'https://pages.xiaohongshu.com/goods/{}'.format(
                        self.__goods_id)
                    trace = '小红书商品: {} 下架了'.format(msg_url)
                    processor_logger.info(trace)
                else:
                    msg_url = 'https://pages.xiaohongshu.com/goods/{}'.format(
                        self.__goods_id)
                    trace = '小红书商品: {} 上架了'.format(msg_url)
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

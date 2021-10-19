from pyspider.helper.string import merge_str
from pyspider.libs.base_crawl import *
from monitor_icy_comments_migrate.config import *
from pyspider.helper.date import Date

import json


class StoreJDExists(BaseCrawl):
    URL = 'https://sclub.jd.com/comment/productPageComments.action?score=0&sortType=5&pageSize=10'

    def __init__(self, goods_id, barcode, page_no=1):
        super(StoreJDExists, self).__init__()
        self.__goods_id = goods_id
        self.__page_no = page_no
        self.__barcode = barcode
        self.__shop_type = 3

    def crawl_builder(self):
        return CrawlBuilder() \
            .set_url(self.URL) \
            .set_headers_kv('User-Agent', USER_AGENT) \
            .set_get_params_kv('productId', self.__goods_id) \
            .set_get_params_kv('page', self.__page_no - 1) \
            .schedule_priority(SCHEDULE_LEVEL_FIRST)

    def parse_response(self, response, task):
        doc = response.text
        try:
            js_result = json.loads(doc)

            # last_page 代表评论总页数
            last_page = js_result.get('maxPage')
            comments = js_result.get('comments')
            processor_logger.info('评论总数：{}'.format(last_page))

            if comments:
                processor_logger.info('开始解析京东评论')
                if self.__page_no < last_page:
                    processor_logger.info('有下一页，第{}页'.format(self.__page_no + 1))
                    self.crawl_handler_page(
                        StoreJDExists(self.__goods_id, self.__barcode, self.__page_no + 1))
                else:
                    processor_logger.info('没有下一页了')

                for _c in comments:
                    create_time = Date.now().format()
                    self.send_message(
                        {
                            'goodsId': self.__goods_id,
                            'id': self.__barcode,
                            'commentsId': _c['id'],
                            'shop_type': self.__shop_type,
                            'content': {
                                'text': _c['content'],
                                'details': _c['referenceName'],
                                'time': _c['creationTime'],
                                'pic': ['https:' + _['imgUrl'] for _ in _c.get('images', '')]
                            },
                            'createTime': create_time,
                            'score': _c['score'],
                            'result': _c
                        },
                        merge_str('jd', self.__goods_id, _c['id'])
                    )
            else:
                processor_logger.info('没有京东评论')
        except Exception as e:
            processor_logger.info(e)
            processor_logger.info('不存在的商品')
        return {
            'result': response.text,
            'response length': len(response.content)
        }

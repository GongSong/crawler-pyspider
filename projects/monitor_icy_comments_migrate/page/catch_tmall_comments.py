import uuid

from monitor_icy_comments_migrate.model.barcode_es import BarcodeES
from pyspider.helper.string import merge_str
from pyspider.libs.base_crawl import *
from pyspider.helper.logging import processor_logger
from monitor_icy_comments_migrate.config import *
from pyspider.helper.date import Date
from cookie.model.data import Data as CookieData


class CatchTmallComments(BaseCrawl):
    URL = 'https://seller-rate.tmall.com/evaluation/GetEvaluations.do?_input_charset=utf-8'

    def __init__(self, account, page=1):
        super(CatchTmallComments, self).__init__()
        self.__account = account
        self.__page = page
        self.__shop_type = 2

    def crawl_builder(self):
        my_cookies = CookieData.get(CookieData.CONST_PLATFORM_TMALL_BACK_COMMENT, self.__account)
        tb_token = my_cookies.split('_tb_token_=', 1)[1].split(';', 1)[0]
        start_time = Date.now().plus_days(-ICY_COMMENTS_START_DAYS).format(full=False)
        end_time = Date.now().plus_days(-ICY_COMMENTS_END_DAYS).format(full=False)
        return CrawlBuilder() \
            .set_url(self.URL) \
            .set_headers_kv('User-Agent', USER_AGENT) \
            .set_cookies(my_cookies) \
            .set_method('POST') \
            .set_post_data_kv('pageNum', self.__page) \
            .set_post_data_kv('type', 'all') \
            .set_post_data_kv('feedType', 'mainFeed') \
            .set_post_data_kv('orderType', 'gmtCreate,desc') \
            .set_post_data_kv('explainType', 'allExplain') \
            .set_post_data_kv('startTime', start_time) \
            .set_post_data_kv('endTime', end_time) \
            .set_post_data_kv('hasPic', 0) \
            .set_post_data_kv('hasVideo', 0) \
            .set_post_data_kv('validRate', 0) \
            .set_post_data_kv('_tb_token_', tb_token) \
            .schedule_priority(SCHEDULE_LEVEL_FIRST) \
            .set_task_id(uuid.uuid4())

    def parse_response(self, response, task):
        js_result = response.json
        assert js_result, '淘宝天猫渠道的icy评论解析失败'
        processor_logger.info('js_result: {}'.format(js_result))
        processor_logger.info('正解析第: {} 页的数据'.format(self.__page))

        # 页码总数
        page_count = js_result['data']['pageCount']

        # 抓取下一页
        if self.__page < page_count:
            processor_logger.info('抓取下一页')
            self.crawl_handler_page(CatchTmallComments(self.__account, page=self.__page + 1))
        else:
            processor_logger.warning('没有下一页了')

        # 解析评论详情
        order_list = js_result['data']['orderList']
        for _c in order_list:
            create_time = Date.now().format()
            goods_id = _c['productId']
            try:
                barcode = self.get_barcode_by_id(self.__shop_type, goods_id)
            except Exception as e:
                processor_logger.error('tmall backstage comments error: {}'.format(e))
                continue
            comments_list = _c['evaluationList']
            sku_info = ''
            for comment in comments_list:
                comments_id = comment['evaluationId']
                comments_time = comment['evaluationTime']
                comments_time = Date(comments_time / 1000).format()
                comment_content = comment['evaluationContent']
                sku_info_c = comment.get('skuInfo')
                if sku_info_c:
                    sku_info = sku_info_c
                pic_list = ['https:' + c for c in comment['evaluationPics']]
                processor_logger.info('send message .....')
                self.send_message(
                    {
                        'goodsId': goods_id,
                        'id': barcode,
                        'commentsId': comments_id,
                        'shop_type': self.__shop_type,
                        'content': {
                            'text': comment_content,
                            'details': sku_info,
                            'time': comments_time,
                            'pic': pic_list,
                        },
                        'createTime': create_time,
                        'score': 0,
                        'result': _c
                    },
                    merge_str('tmall', goods_id, comments_id)
                )
        return {
            'account': self.__account,
            'page': self.__page,
        }

    def get_barcode_by_id(self, shop_type, goods_id):
        """
        从es里拿barcode
        :param shop_type:
        :param goods_id:
        :return:
        """
        result = BarcodeES().find_barcode_by_goods_id(shop_type, goods_id)
        if result:
            return result[0]['_source']['goodsCode']
        else:
            return ''

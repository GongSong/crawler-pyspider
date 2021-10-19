from monitor_icy_comments_migrate.page.taobao_comment_goods import TaoBaoCommentsGoods
from pyspider.libs.base_crawl import *
from pyspider.helper.logging import processor_logger
from monitor_icy_comments_migrate.config import *
from cookie.model.data import Data as CookieData
from bs4 import BeautifulSoup


class CatchTaoBaoComments(BaseCrawl):
    URL = 'https://rate.taobao.com/user-myrate-UvCIbMCx4vFHYvWTT--banner%7C1--receivedOrPosted%7C0' \
          '--buyerOrSeller%7C0--currentPage%7C{}--maxPage%7C5.htm?rateList'

    def __init__(self, account, page_no=1):
        super(CatchTaoBaoComments, self).__init__()
        self.__page_no = page_no
        self.__shop_type = 1
        self.__account = account
        self.__shop_url = self.URL.format(self.__page_no)

    def crawl_builder(self):
        return CrawlBuilder() \
            .set_url(self.__shop_url) \
            .set_headers_kv('User-Agent', USER_AGENT) \
            .set_cookies(CookieData.get(CookieData.CONST_PLATFORM_TAOBAO_BACK_COMMENT, self.__account)) \
            .schedule_priority(SCHEDULE_LEVEL_SECOND)

    def parse_response(self, response, task):
        doc = response.text
        soup = BeautifulSoup(doc, 'lxml')
        delay_time = 1

        comment_items = soup.find_all('tr', class_='J_RateItem')
        if comment_items:
            # 有下一页
            self.crawl_handler_page(CatchTaoBaoComments(self.__account, self.__page_no + 1))
        for comment in comment_items:
            # 淘宝的好评还是差评
            comment_quality = comment.find('td', class_='align-c').find('i').attrs['title']
            # 评论ID
            comment_id = comment.attrs['data-id']
            # 评论内容
            comment_content = comment.find_all('p', class_='comment')
            comment_content = ';'.join([_.get_text().strip() for _ in comment_content])
            # 评论对应的商品 url
            goods_url = 'https:' + comment.find_all('td')[3].find('a').attrs['href'].replace('tradearchive', 'trade')
            # 评论时间
            comment_date = comment.find('p', class_='date').get_text()[1:-1]
            # 评论图片
            comment_pics = comment.find('ul', class_='photos')
            comment_pic = ['https:' + _.find('a').attrs['href'] for _ in
                           comment_pics.find_all('li')] if comment_pics else []
            data = {
                "commentsId": comment_id,
                "content": {
                    "pic": comment_pic,
                    "text": comment_content,
                    "time": comment_date
                },
                "score": 0,
                "shop_type": self.__shop_type,
                "comment_quality": comment_quality,
            }

            self.crawl_handler_page(TaoBaoCommentsGoods(goods_url, self.__account, comment_id, delay_time, data))
            delay_time += 1
        return {
            'msg': '完成淘宝后台评论第: {} 页的抓取'.format(self.__page_no),
            'response length': len(response.content),
            'result': response.text
        }

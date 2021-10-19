from alarm.page.ding_talk import DingTalk
from backstage_data_migrate.config import *
from backstage_data_migrate.page.tmall_huoniu_result import HuoniuResult
from pyspider.helper.date import Date
from pyspider.helper.logging import processor_logger
from pyspider.libs.base_crawl import BaseCrawl
from pyspider.libs.crawl_builder import CrawlBuilder
from cookie.model.data import Data as CookieData
from pyspider.libs.utils import md5string


class HuoniuInventory(BaseCrawl):
    """
    发送获取 天猫火牛 仓库中和已售完的商品 的下载请求
    """
    HUONIU_URL = 'https://mobile.kaquanbao.com/product/huoniu/rel/index.php?s=/Items/Index/inventory/tid/{}'

    def __init__(self, username, banner='for_shelved', delist_type='all_shelf', delay_second=None):
        super(HuoniuInventory, self).__init__()
        self.__username = username
        self.__banner = banner
        self.__delist_type = delist_type
        self.__delay_second = delay_second

    def crawl_builder(self):
        cookie = CookieData.get(CookieData.CONST_PLATFORM_TAOBAO_HUONIU, self.__username)
        huoniu_cookie, huoniu_token = cookie.split(':token', 1)
        huoniu_url = self.HUONIU_URL.format(huoniu_token)
        builder = CrawlBuilder() \
            .set_url(huoniu_url) \
            .set_cookies(huoniu_cookie) \
            .set_headers_kv('User-Agent', USER_AGENT) \
            .set_post_data_kv('page', 1) \
            .set_post_data_kv('page_size', 10) \
            .set_post_data_kv('keyword', '') \
            .set_post_data_kv('seller_cids', '') \
            .set_post_data_kv('banner', self.__banner) \
            .set_post_data_kv('delist_type', self.__delist_type) \
            .set_post_data_kv('has_discount', '') \
            .set_post_data_kv('showcase', '') \
            .set_post_data_kv('is_export', 1) \
            .set_post_data_kv('export_title', 'num_iid,outer_id') \
            .schedule_age() \
            .set_task_id(md5string(self.__username + huoniu_url))
        if self.__delay_second:
            builder.schedule_delay_second(self.__delay_second)
        return builder

    def parse_response(self, response, task):
        try:
            if int(Date.now().strftime('%H')) > HUONIU_TIME:
                print('天猫火牛爬虫的重试次数过多，时间超过了 {} 点，停止爬虫并发送报警'.format(HUONIU_TIME))
                token = '8d67692c0106afe9379b44df67f9a0b4ecfc24a0fcdcfba4381bc334b550cdfc'
                title = '天猫火牛爬虫抓取失败报警'
                content = '天猫火牛爬虫的重试次数过多，时间超过了 16 点，请重新检查该爬虫的抓取情况'
                self.crawl_handler_page(DingTalk(token, title, content))
                return {
                    'content': response.text,
                    'msg': content,
                    'url': response.url
                }
            text = response.json
            status = int(text['status'])
            log_info = text['loginfo']
            print(log_info)
            if status == 1:
                # success
                print('success')
                if self.__delist_type == '':
                    self.crawl_handler_page(HuoniuResult(self.__username))
                    return {
                        'msg': '发完了本日的商品ID对应关系的请求'
                    }
                self.crawl_handler_page(
                    HuoniuInventory(self.__username, banner='sold_out', delist_type='', delay_second=60))
            else:
                # failed
                print('failed')
                self.crawl_handler_page(HuoniuInventory(self.__username, delay_second=60))
        except Exception as e:
            print(e)
            print('没有拿到正确的 cookie, 请检查 cookie 更新的脚本')
            token = '8d67692c0106afe9379b44df67f9a0b4ecfc24a0fcdcfba4381bc334b550cdfc'
            title = '天猫火牛 cookie 获取失败报警'
            content = '天猫火牛没有拿到正确的 cookie, 请检查 cookie 更新的脚本'
            self.crawl_handler_page(DingTalk(token, title, content))

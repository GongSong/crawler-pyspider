from common_crawler.config import IMAGE_TIMEOUT, IMAGE_CONNECT_TIMEOUT, USER_AGENT
from pyspider.libs.base_crawl import *
from pyspider.helper.ips_pool import IpsPool
from pyspider.libs.oss import oss_cdn


class ImageDownload(BaseCrawl):
    """
    图片下载 公共爬虫
    """

    def __init__(self, url, oss_img_path="", cookies="", use_proxy=False, priority=0):
        """

        :param url: 图片地址
        :param oss_img_path: 上传到oss的地址
        :param cookies: cookies
        :param use_proxy: 是否使用代理，默认不使用
        :param priority: 抓取优先级
        """
        super(ImageDownload, self).__init__()
        self.__url = url
        self.__oss_img_path = oss_img_path
        self.__cookies = cookies
        self.__use_proxy = use_proxy
        self.__priority = priority

    def crawl_builder(self):
        builder = CrawlBuilder() \
            .set_url(self.__url) \
            .set_headers_kv('User-Agent', USER_AGENT) \
            .set_timeout(IMAGE_TIMEOUT) \
            .set_connect_timeout(IMAGE_CONNECT_TIMEOUT) \
            .schedule_priority(self.__priority) \
            .set_task_id(md5string(self.__url))

        if self.__cookies:
            builder.set_cookies(self.__cookies)

        if self.__use_proxy:
            builder.set_proxy(IpsPool.get_ip_from_pool())

        return builder

    def parse_response(self, response, task):
        if response.status_code == 200 and self.__oss_img_path:
            oss_cdn.upload_data(self.__oss_img_path, response.content)

        return {
            'crawler_name': 'ImageDownload',
            'url': self.__url,
            'oss_img_path': self.__oss_img_path,
        }

from blog_spider.config import *
from pyspider.helper.string import merge_str
from pyspider.libs.base_crawl import *
from pyspider.helper.ips_pool import IpsPool
from pyspider.libs.oss import oss_cdn


class BlogImgDown(BaseCrawl):
    """
    博客图片下载
    """

    def __init__(self, url, img_path, use_proxy=False, priority=0):
        super(BlogImgDown, self).__init__()
        self.__url = url
        self.__img_path = img_path
        self.__use_proxy = use_proxy
        self.__priority = priority

    def crawl_builder(self):
        builder = CrawlBuilder() \
            .set_url(self.__url) \
            .set_headers_kv('User-Agent', USER_AGENT) \
            .set_timeout(GOODS_TIMEOUT) \
            .set_connect_timeout(GOODS_CONNECT_TIMEOUT) \
            .schedule_priority(self.__priority) \
            .set_task_id(merge_str(self.__url.split('/')[-1]))

        if self.__use_proxy:
            builder.set_proxy(IpsPool.get_ip_from_pool())

        return builder

    def parse_response(self, response, task):
        if response.status_code == 200:
            oss_cdn.upload_data(self.__img_path, response.content)

        return {
            'unique_name': 'blog_img',
            # 'content': response.content
        }

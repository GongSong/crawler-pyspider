from pyspider.libs.base_crawl import *


class Test(BaseCrawl):
    URL = 'https://www.baidu.com'

    def __init__(self):
        super(Test, self).__init__()

    def crawl_builder(self):
        return CrawlBuilder() \
            .set_url(self.URL) \
            .set_kwargs_kv('validate_cert', False)

    def parse_response(self, response, task):
        return {'result': response.text}

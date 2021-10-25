import uuid

from hack_project.config import def_headers
from pyspider.libs.base_crawl import *


class WafCheck(BaseCrawl):
    """
    检测waf
    """
    xsstring = '<script>alert("XSS");</script>'
    sqlistring = "UNION SELECT ALL FROM information_schema AND ' or SLEEP(5) or '"
    lfistring = '../../../../etc/passwd'
    rcestring = '/bin/cat /etc/passwd; ping 127.0.0.1; curl google.com'
    xxestring = '<!ENTITY xxe SYSTEM "file:///etc/shadow">]><pwn>&hack;</pwn>'

    def __init__(self, url):
        super(WafCheck, self).__init__()
        self.url = url

    def crawl_builder(self):
        builder = CrawlBuilder() \
            .set_url(self.url) \
            .set_headers(def_headers) \
            .set_get_params_kv('s', self.xsstring) \
            .set_task_id(uuid.uuid4())
        return builder

    def parse_response(self, response, task):
        print("response:{}".format(response.text))
        status_code = response.status_code
        redirect_url = response.url
        return {
            'status_code': status_code,
            'redirect_url': redirect_url,
        }


if __name__ == '__main__':
    WafCheck("www.baidu.com").get_result()

from cookie.config import *
from pyspider.libs.base_crawl import *
from cookie.model.data import Data as CookieData


class LandongLogin(BaseCrawl):
    """
    landong 的登录
    """

    URL = '{landong_host}/Login?ReturnUrl=/'

    def __init__(self, username, password, token=None, cookies=None):
        super(LandongLogin, self).__init__()
        self.username = username
        self.password = password
        self.token = token
        self.cookies = cookies

    def crawl_builder(self):
        landong_host = config.get('landong', 'page_host')
        builder = CrawlBuilder() \
            .set_url(self.URL.format(landong_host=landong_host) + "#{}:{}".format(self.username, self.token[:5] if self.token else "")) \
            .set_headers_kv('User-Agent', USER_AGENT)
        if self.cookies:
            post_data = {
                "__RequestVerificationToken": self.token,
                "CultureName": "zh-CN",
                "ClientId": config.get('landong', 'client_id'),
                "UserAccount": self.username,
                "Password": self.password,
                "RememberMe": "true",
            }
            builder.set_headers_kv("Cookie", "__RequestVerificationToken={}".format(self.token))
            builder.set_cookies_dict(self.cookies)
            builder.set_post_data(post_data)
        return builder

    def parse_response(self, response, task):
        content = response.text
        status_code = response.status_code
        redirect_url = response.url

        # 初始cookie
        res_cookies = response.cookies

        if not self.cookies:
            # 第二个cookie
            if "__RequestVerificationToken" not in content:
                raise Exception("获取 hidden RequestVerificationToken 失败")
            init_content = content.split("<input name=\"__RequestVerificationToken\"", 1)
            if len(init_content) > 1 and "value=" in init_content[1]:
                token = init_content[1].split("value=\"", 1)[1].split("\"", 1)[0]
            else:
                raise Exception("获取__RequestVerificationToken失败")
            # 登录
            self.crawl_handler_page(LandongLogin(self.username, self.password, token, res_cookies))
        else:
            # 保存登录后的cookie
            cookies_str = "; ".join([str(x) + "=" + str(y) for x, y in res_cookies.items()])
            CookieData.set(CookieData.CONST_PLATFORM_LANDONG, self.username, cookies_str)
        return {
            'status_code': status_code,
            'redirect_url': redirect_url,
            'res_cookies': res_cookies,
        }

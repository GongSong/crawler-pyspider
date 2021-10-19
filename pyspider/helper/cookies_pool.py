from pyspider.core.model.http_simple import HttpSimple, HttpBase
from pyspider.config import config
from pyspider.helper.date import Date
from pyspider.helper.logging import logger
from pyspider.helper.string import merge_str


class CookiesPool:
    # 本地缓存10秒
    CONST_TTL = 10
    local_cache = {}

    @staticmethod
    def get_cookies_from_pool(website, username, force_remote=False):
        """
        从cookie池获取cookie
        :param website:
        :param username:
        :param force_remote: 是否强制从远程cookie池拉最新的cookie
        :return:
        """
        cookies = CookiesPool.get_local_cookies(website, username)
        if not force_remote and cookies:
            return cookies['data']

        start = Date().now()
        cookies = HttpSimple()\
            .set_url(config.get('cookies_pool', 'service_url'))\
            .set_param('website', website)\
            .set_param('username', username).data
        used_time = Date().now().diff(start)
        if cookies:
            logger.info('获取cookies, website: %s, username: %s, cookies: %s' % (website, username, cookies),
                        extra={'get_cookies': 1, 'used_time': used_time})
            return cookies['data']
        else:
            logger.error('获取cookies, website: %s, username: %s, cookies: %s' % (website, username, cookies),
                         extra={'get_cookies': 1, 'used_time': used_time})
            return ''

    @staticmethod
    def get_local_cookies(website, username):
        cookies = CookiesPool.local_cache.get(merge_str(website, username), {})
        return cookies if cookies and Date().now().diff(cookies['time']) < CookiesPool.CONST_TTL else ''

    @staticmethod
    def set_local_cookies(website, username, cookies):
        cookies['time'] = Date.now()
        CookiesPool.local_cache[merge_str(website, username)] = cookies

    @staticmethod
    def cookies_to_dict(cookies: str):
        """
        cookies str to cookies dict
        :param cookies:
        """
        cookies_list = []
        if "=" not in cookies:
            return cookies_list
        if ";" in cookies:
            cookies_splits = cookies.split(";")
            for item in cookies_splits:
                cookies_list.append({
                    "name": item.split("=", 1)[0].strip(),
                    "value": item.split("=", 1)[1].strip()
                })
        else:
            cookies_list.append({
                "name": cookies.split("=", 1)[0].strip(),
                "value": cookies.split("=", 1)[1].strip(),
            })
        return cookies_list

from cookie.config import HUPUN_COOKIE_POOL_KEY
from cookie.model.data import Data as CookieData
from cookie.platform.taobao.TmallLogin import TmallLogin
from cookie.platform.taobao.tmall_product_price import TmallProductPrice
from pyspider.core.model.storage import default_storage_redis
import hashlib
import fire


class Cron:
    def hupun_cookie_pool(self):
        cookies = default_storage_redis.keys(HUPUN_COOKIE_POOL_KEY + '*')
        print(cookies)
        if len(cookies) < 200:
            for i in range(3, 8):
                value = CookieData.get(CookieData.CONST_PLATFORM_HUPUN,
                                 CookieData.CONST_USER_HUPUN[i][0])
                print(CookieData.CONST_PLATFORM_HUPUN,
                                 CookieData.CONST_USER_HUPUN[i][0])
                print(value)
                name = hashlib.md5(value.encode('utf-8')).hexdigest()
                print(HUPUN_COOKIE_POOL_KEY + name)
                if not default_storage_redis.get(HUPUN_COOKIE_POOL_KEY + name):
                    default_storage_redis.set(HUPUN_COOKIE_POOL_KEY + name, value, ex=14400)

    def tmall_product_price(self):
        TmallProductPrice(["479195376"]).catch_all_goods()

    def tmall_product_cookie(self):
        for account, password in CookieData.CONST_USER_TMALL_PRODUCT:
            TmallLogin(account, password).update_cookies()




if __name__ == '__main__':
    fire.Fire(Cron)
import json
from pyspider.config import config
from pyspider.core.model.storage import default_storage_redis
from pyspider.helper.date import Date
from pyspider.helper.string import merge_str


class Data:
    CONST_PREFIX = 'cookies'
    CONST_PLATFORM_TAOBAO_HUONIU = 'taobao_huoniu'
    CONST_PLATFORM_TAOBAO_SYCM = 'taobao_sycm'
    CONST_PLATFORM_TAOBAO_TBK = 'taobao_tbk'
    CONST_PLATFORM_TAOBAO_MYSELLER = 'taobao_myseller'
    CONST_PLATFORM_TAOBAO_COMMENT = 'taobao_comment'
    CONST_PLATFORM_TMALL_COMMENT = 'tmall_comment'
    CONST_PLATFORM_TAOBAO_BACK_COMMENT = 'taobao_backstage_comment'
    CONST_PLATFORM_TMALL_BACK_COMMENT = 'tmall_backstage_comment'
    CONST_PLATFORM_TMALL_SELLER = 'tmall_seller_cookies'
    CONST_PLATFORM_TAOBAO_SHOP = 'taobao_shop'
    CONST_PLATFORM_TAOBAO_MANAGER_SOFT = 'taobao_manager_soft'
    CONST_PLATFORM_HUPUN = 'hupun'
    CONST_PLATFORM_HUPUN_ORIGIN_COOKIE = 'hupun_origin_cookie'
    CONST_PLATFORM_WEIPINHUI = 'weipinhui'
    CONST_PLATFORM_REDBOOK = 'redbook'
    CONST_PLATFORM_JINGDONG = 'jingdong'
    CONST_PLATFORM_TABLEAU = 'tableau'
    CONST_PLATFORM_TMALL_PRODUCT = 'tmall_product'
    CONST_PLATFORM_TMALL_GOODS = 'tmall_goods'
    CONST_PLATFORM_TMALL_SHOP_GOODS = 'tmall_shop_goods'
    CONST_PLATFORM_LANDONG = 'landong'

    CONST_USER_TAOBAO_HUONIU = [('icy旗舰店:研发', 'ICY20180827')]
    CONST_USER_SYCM_BACKSTAGE = [('icy旗舰店:研发', 'ICY20180827', 'tmall')]
    CONST_USER_TAOBAO_TBK = [('icy旗舰店:it', 'ICY123456')]
    CONST_USER_TAOBAO_MYSELLER = [('炫时科技:研发1', 'youmengicy2018')]
    CONST_USER_TAOBAO_MANAGER_SOFT = [('icy旗舰店:研发', 'ICY20180827', 'tmall_flagship'), ('icyoutlets店:研发', 'yourdream666', 'tmall_outlets')]
    CONST_USER_TMALL_BACK_COMMENT = [('icy旗舰店:研发', 'ICY20180827')]
    CONST_USER_TAOBAO_BACK_COMMENT = [('炫时科技:研发1', 'youmengicy2018')]  # [('炫时科技', 'yourdream2018')]
    CONST_USER_HUPUN = [
        (config.get('hupun', 'username_erp1'), config.get('hupun', 'password_erp1')),
        (config.get('hupun', 'username_erp2'), config.get('hupun', 'password_erp2')),
        (config.get('hupun', 'username_erp3'), config.get('hupun', 'password_erp3')),
        (config.get('hupun', 'username_erp4'), config.get('hupun', 'password_erp4')),
        (config.get('hupun', 'username_erp5'), config.get('hupun', 'password_erp5'))
    ]
    CONST_USER_LANDONG = [
        (config.get('landong', 'username_landong1'), config.get('landong', 'password_landong1')),
    ]
    CONST_USER_WEIPINHUI = [('min.hu@yourdream.cc', 'Yourdream123!')]
    CONST_USER_REDBOOK_BACKSTAGE = [('Wendy@yourdream.cc', 'yourdream@2020')]
    CONST_USER_REDBOOK_BLOGGER_LIVE = [('huilin.xu@yourdream.cc', 'Xuhuilin1997'), ('jingyi.li@yourdream.cc', 'ICYjingyi123'), ('xiaoli.wang@yourdream.cc', 'wobuzhidao1!')]
    CONST_USER_JINGDONG = [('icy-05', 'yourdream123')]
    CONST_USER_TAOBAO_SHOP = [('taobao:shop:goods', 'yourdream123')]
    CONST_USER_TABLEAU = [('admin', 'Shyourdream4U')]
    CONST_USER_JD_BACKSTAGE = '穿衣助手旗舰店'
    CONST_USER_TMALL_PRODUCT = [('icy旗舰店:研发', 'ICY20180827')]

    CONST_COMMON_TMALL_SHOP = "common_tmall_shop_cookies"
    CONST_COMMON_TMALL_GOODS = "common_tmall_goods_cookies"
    CONST_HUPUN_LOGIN_DOMIN = 'https://erp.hupun.com/'

    @staticmethod
    def set(platform, username, cookies: str):
        default_storage_redis.set(Data.__format_key(platform, username), cookies)

    @staticmethod
    def get(platform, username):
        return default_storage_redis.get(Data.__format_key(platform, username))

    @staticmethod
    def srand(platform):
        """
        指定平台随机拿一个cookie
        :param platform:
        :return: cookies string
        """
        data = default_storage_redis.srandmember(Data.__format_key(platform))
        if not data:
            return None
        return json.loads(data)['cookies']

    @staticmethod
    def sadd(platform, cookies: str):
        """
        指定平台添加一个cookie
        :param platform:
        :param cookies:
        :return:
        """
        default_storage_redis.sadd(Data.__format_key(platform),
                                   json.dumps({'time': Date.now().timestamp(), 'cookies': cookies}))

    @staticmethod
    def smembers(platform):
        """
        指定平台拿全部cookie
        :param platform:
        :return:
        """
        data = default_storage_redis.smembers(Data.__format_key(platform))
        if not data:
            return []
        rtn = []
        for _ in data:
            rtn.append(json.loads(_.decode('utf-8')))
        return rtn

    @staticmethod
    def srem(platform, cookies: str):
        """
        指定平台删除指定cookie
        :param platform:
        :param cookies:
        :return:
        """
        key = Data.__format_key(platform)
        for _ in Data.smembers(key):
            if _['cookies'] == cookies:
                default_storage_redis.srem(key, json.dumps(_))

    @staticmethod
    def sexpire_del(platform, expire=300):
        """
        指定平台删除过期的cookie
        :param platform:
        :param expire:
        :return:
        """
        key = Data.__format_key(platform)
        min_time = Date.now().timestamp() - expire
        for _ in Data.smembers(platform):
            if _['time'] < min_time:
                default_storage_redis.srem(key, json.dumps(_))

    @staticmethod
    def __format_key(platform, username=''):
        return merge_str(Data.CONST_PREFIX, platform, username)

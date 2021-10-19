from cookie.platform.taobao.login_base import *


class Tbk(LoginBase):
    """
    阿里妈妈, 主要是拿淘宝客和广告位信息
    """
    URL = 'https://login.taobao.com/member/login.jhtml?style=mini&newMini2=true&from=alimama&redirectURL=http%3A%2F%2Flogin.taobao.com%2Fmember%2Ftaobaoke%2Flogin.htm%3Fis_login%3d1&full_redirect=true&disableQuickLogin=true'

    def __init__(self, username, password):
        super(Tbk, self).__init__(self.URL, username, password, CookieData.CONST_PLATFORM_TAOBAO_TBK)
        self.set_last_url('https://pub.alimama.com/')


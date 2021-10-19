from cookie.platform.taobao.login_base import *


class Myseller(LoginBase):
    """
    卖家中心, 淘宝后台订单数据下载
    """
    URL = 'https://login.taobao.com/member/login.jhtml?redirectURL=http%3A%2F%2Ftrade.taobao.com%2Ftrade%2Fitemlist%2Flist_export_order.htm%3Fpage_no%3D1'

    def __init__(self, username, password):
        super(Myseller, self).__init__(self.URL, username, password, CookieData.CONST_PLATFORM_TAOBAO_MYSELLER)
        self.set_last_url('https://myseller.taobao.com/home.htm')


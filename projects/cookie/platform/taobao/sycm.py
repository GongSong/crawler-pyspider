from cookie.platform.taobao.login_base import *


class Sycm(LoginBase):
    """
    生意参谋
    """
    URL = 'https://login.taobao.com/member/login.jhtml?from=sycm&full_redirect=true&style=minisimple&minititle=&minipara=0,0,0&sub=true&redirect_url=http://sycm.taobao.com/bda/items/effect/item_effect.htm?spm=a21ag.7634348.LeftMenu.d248.79ac71736jYMHM'
    # PROXY = '10.0.5.58:3128'
    PROXY = ''

    def __init__(self, username, password):
        super(Sycm, self).__init__(self.URL, username, password, CookieData.CONST_PLATFORM_TAOBAO_SYCM,
                                   proxy=self.PROXY)
        self.set_last_url('https://sycm.taobao.com/cc/macroscopic_monitor#item-rank')
        self.set_check_class_tag('menu-list')

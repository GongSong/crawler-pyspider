from cookie.platform.taobao.login_base import *


class TmallBackComment(LoginBase):
    """
    天猫后台的评论信息
    """
    URL = 'https://login.taobao.com/member/login.jhtml?redirectURL=http://seller-rate.tmall.com/evaluation/allRate.htm'

    def __init__(self, username, password):
        super(TmallBackComment, self).__init__(self.URL, username, password,
                                               CookieData.CONST_PLATFORM_TMALL_BACK_COMMENT)
        self.set_last_url('https://seller-rate.tmall.com/evaluation/allRate.htm')
        self.set_check_class_tag('service-button-container')

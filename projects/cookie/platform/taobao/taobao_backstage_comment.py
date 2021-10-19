from cookie.platform.taobao.login_base import *


class TaobaoBackComment(LoginBase):
    """
    淘宝后台的评论信息
    可能会出现登录失败，有滑动验证码，导致获取到无效的cookie，拿不到淘宝评论数据
    """
    URL = 'https://login.taobao.com/member/login.jhtml?redirectURL=http%3A%2F%2Frate.taobao.com%2Fuser-myrate-UvCIb' \
          'MCx4vFHYvWTT--banner%257C1--receivedOrPosted%257C0--buyerOrSeller%257C0.htm%3Fspm%3Da313o.201708ban.sell' \
          'er-qn-head.3.64f0197aMKjCky%26user_id%3DUvCIbMCx4vFHYvWTT%26banner%3D1%26receivedOrPosted%3D0%26buyerOrS' \
          'eller%3D0'

    def __init__(self, username, password):
        super(TaobaoBackComment, self).__init__(self.URL, username, password,
                                                CookieData.CONST_PLATFORM_TAOBAO_BACK_COMMENT)
        self.set_last_url(
            'https://rate.taobao.com/user-myrate-UvCIbMCx4vFHYvWTT--banner%7C1--receivedOrPosted%7C0--buyerOrSeller'
            '%7C0.htm?rateList')

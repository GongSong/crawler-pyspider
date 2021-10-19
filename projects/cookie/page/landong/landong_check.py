from cookie.page.landong.landong_login import LandongLogin
from landong.page.base import Base
from pyspider.helper.date import Date


class LandongCookieCheck(Base):
    """
    通过获取账号的个人信息来判断 cookie 是否有效
    """
    PATH = "/Sys/PersonalCenter/IndAccountManagement?containerId=Sys_PersonalCenter-PersonalCenterFormContainer"

    def __init__(self, username, password):
        super(LandongCookieCheck, self).__init__()
        self.username = username
        self.password = password

    def get_unique_define(self):
        return str(Date.now().timestamp())

    def get_api_route(self):
        return self.PATH

    def parse_response(self, response, task):
        result = response.text
        if "用户名称" in result and "授权名称" in result:
            return {
                'msg': "成功登录",
                'response': response.text
            }
        else:
            self.crawl_handler_page(LandongLogin(self.username, self.password))
            return {
                "err_msg": '澜东云账号的cookie已失效, 请重新登录',
                'response': response.text
            }

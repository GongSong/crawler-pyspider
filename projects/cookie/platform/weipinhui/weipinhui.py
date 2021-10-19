from cookie.platform.weipinhui.login_base import *


class Weipinhui(LoginBase):
    """
    唯品会商家后台
    """
    URL = 'http://compass.vis.vip.com/new/dist/web/index.html?__token__=eyJ0b2tlbiI6IjU4MGI5OTMyYzA4MDBlYjY0MWNjNT' \
          'FjZTU0YjM4MWVmIiwidG9rZW4xIjoiOTUxZDBkMTBhMzEzYmU5ZTZjOWM3NTQ5MWQzZmY1MWQiLCJ2ZW5kb3JJZCI6IjI4NTI2Iiwid' \
          'XNlck5hbWUiOiI2MTM2MDUiLCJ2ZW5kb3JDb2RlIjoiNjEzNjA1IiwidXNlcklkIjoiODYyNTQiLCJ2aXNTZXNzaW9uSWQiOiJiaWQ1' \
          'dGhnajQ4amdha2h1ODRxcDZkdXVvMyIsImFwcE5hbWUiOiJ2aXNQQyIsInZpc2l0RnJvbSI6InZjIn0=#/product/details'

    def __init__(self, username, password):
        super(Weipinhui, self).__init__(self.URL, username, password, CookieData.CONST_PLATFORM_WEIPINHUI)
        self.set_last_url(self.URL)

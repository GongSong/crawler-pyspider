from cookie.page.hupun_login_account import HupunLoginAccount
from hupun.page.base import *


class HCookieCheck(Base):
    """
    通过获取账号的个人信息来判读 cookie 是否有效
    现在是通过请求【我的下载】标签来确定cookie是否有效
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
  "action": "load-data",
  "dataProvider": "documentInterceptor#queryExportTask",
  "supportsEntity": true,
  "parameter": {
    "startDate": "%s",
    "endDate": "%s",
    "$dataType": "dtExportTaskSearch"
  },
  "resultDataType": "v:downloadCalf$[dtExportTask]",
  "pageSize": 10,
  "pageNo": 1,
  "context": {},
  "loadedDataTypes": [
    "dtExportTask",
    "dtExportType",
    "dtExportTaskSearch"
  ]
 }
]]></request>
</batch>
"""

    def __init__(self, username, password):
        super(HCookieCheck, self).__init__()
        self.__username = username
        self.__password = password

    def get_request_data(self):
        start_date = Date.now().plus_days(-1).format_es_old_utc()
        end_date = Date.now().format_es_old_utc()
        return self.request_data % (start_date, end_date)

    def get_unique_define(self):
        return merge_str('hupun_cookie_check', self.__username)

    def parse_response(self, response, task):
        # json 结果
        try:
            result = self.detect_xml_text(response.text)
            if len(result['data']):
                oper_nick = result['data']['entityCount']
                # 取消更新老的 hupun cookies 池
                # cookies = CookieData.get(CookieData.CONST_PLATFORM_HUPUN, CookieData.CONST_USER_HUPUN[0][0])
                # self.crawl_handler_page(UpdateOldCookie(cookies, self.CONST_PRIORITY_BUNDLED))
                return {
                    'msg': '已成功登录万里牛',
                    'content_length': len(response.content),
                    'text': response.text,
                }
            else:
                assert False, '万里牛的cookie已失效, 请重新登录'
        except Exception as e:
            processor_logger.warning('万里牛的cookie已失效: {}，请重新登录'.format(e))
            self.crawl_handler_page(HupunLoginAccount(self.__username, self.__password))
            return {
                'msg': '万里牛的cookie已失效: {}，请重新登录'.format(e),
                'response': response.text,
            }

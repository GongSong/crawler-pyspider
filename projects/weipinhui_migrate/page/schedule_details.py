from alarm.page.ding_talk import DingTalk
from pyspider.libs.base_crawl import *
from cookie.model.data import Data as CookieData
from weipinhui_migrate.config import *


class ScheduleDetails(BaseCrawl):
    URL = 'http://compass.vis.vip.com/dangqi/details/downloadDangqiDetails?brandStoreName=ICY&brandName=%E5%94%AF%E5' \
          '%93%81%E4%BC%9A%E8%AE%BE%E8%AE%A1%E5%B8%88%E9%9B%86%E5%90%88%E6%97%97%E8%88%B0%E5%BA%97-20190214&surrogat' \
          'eBrandId=303692788&brandType=%E6%97%97%E8%88%B0%E5%BA%97&filter=orderCnt%2CavgOrderAmount%2CuserCnt%2Cgoo' \
          'dsCnt%2CsalesAmount%2CsaleStockAmtOnline%2CuvConvert%2CactiveName%2CsaleMode%2CsaleTimeFrom%2CsaleTimeTo%' \
          '2CavgGoodsAmount%2CgoodsActureAmt%2CsaleCntNoReject%2CsalesAmountNoCutReject%2CgoodsMoney%2CcutGoodsMoney' \
          '%2CrejectedGoodsAmount%2CrejectedGoodsAmountPercent%2CrejectedGoodsCutMoney%2CbackGoodsAmount%2CbackGoods' \
          'AmountPercent%2CbackGoodsCutMoney%2CbackRejectedGoodsAmountPercent%2CavgArrivalToShipHours%2ConlineStockA' \
          'mt%2ConlineStockCnt&mixBrand=0&sortColumn=logDate&sortType=1&pageSize={0}&pageNumber={1}&sumType=1&lv3Cat' \
          'egoryFlag=0&optGroupFlag=0&warehouseFlag=0&analysisType=2&dateMode={2}&dateType=D&detailType={3}&beginDat' \
          'e={4}&endDate={5}'

    def __init__(self, account, date_mode, detail_type, begin_date, end_date, save_type, catch_next_page=False):
        """
        唯品会 档期详情数据 分天查看的表格下载
        :param account:
        :param date_mode:
        :param detail_type:
        :param begin_date:
        :param end_date:
        :param save_type:
        :param catch_next_page:
        """
        super(ScheduleDetails, self).__init__()
        self.__account = account
        self.__date_mode = date_mode
        self.__detail_type = detail_type
        self.__begin_date = begin_date
        self.__end_date = end_date
        self.__save_type = save_type
        self.__page_number = PAGE_NUMBER
        self.__page_size = PAGE_SIZE
        self.__catch_next_page = catch_next_page
        self.__url = self.URL.format(self.__page_size, self.__page_number, self.__date_mode, self.__detail_type,
                                     self.__begin_date,
                                     self.__end_date)

    def crawl_builder(self):
        return CrawlBuilder() \
            .set_url(self.__url) \
            .set_cookies(CookieData.get(CookieData.CONST_PLATFORM_WEIPINHUI, self.__account)) \
            .set_headers_kv('User-Agent', USER_AGENT)

    def parse_response(self, response, task):
        headers = response.headers
        if 'Content-Disposition' not in headers or 'attachment' not in headers['Content-Disposition']:
            processor_logger.error('cookie error')
            title = '唯品会 档期详情数据 下载文件爬虫报警'
            text = '唯品会 档期详情数据 下载文件爬虫未抓取到 {} 的文件数据，请检查 Mac-Pro 上的 cookie 获取模块'.format(
                self.__begin_date + '|' + self.__end_date)
            self.crawl_handler_page(DingTalk(ROBOT_TOKEN, title, text))
            return {
                'msg': text,
                'content length': len(response.content)
            }
        account_path = '档期详情/{save_type}/档期明细_{begin_date}-{end_date}.xlsx'.format(save_type=self.__save_type,
                                                                                   begin_date=self.__begin_date,
                                                                                   end_date=self.__end_date)
        file_path = oss.get_key(oss.CONST_WEIPINHUI_PATH, account_path)
        oss.upload_data(file_path, response.content)
        return {
            'msg': '已获取了{}{}-{}的数据'.format(self.__save_type, self.__begin_date, self.__end_date),
            'content length': len(response.content)
        }

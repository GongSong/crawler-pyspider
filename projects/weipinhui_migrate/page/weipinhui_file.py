from alarm.page.ding_talk import DingTalk
from pyspider.helper.excel_reader import ExcelReader
from pyspider.libs.base_crawl import *
from cookie.model.data import Data as CookieData
from weipinhui_migrate.config import *
from weipinhui_migrate.model.weipinhui import Weipinhui


class WeipinhuiFile(BaseCrawl):
    URL = 'http://compass.vis.vip.com/newGoods/details/downloadGoodsDetails'
    FILTER = 'userCnt,goodsActureAmt,bareSalesAmt,bareSalesAmtWithoutRejectedReturned,bareSalesAmtRejectedReturne' \
             'd,goodsCnt,goodsCntWithoutReturn,goodsMoney,goodsAmt,goodsAmtWithoutReturn,sellingRatio,couponAmoun' \
             't,goodsActureAmtWithRejectedReturned,goodsActureAmtWithoutRejectedReturned,onSaleStockAmt,onSaleSto' \
             'ckCnt,lv3Category,vipshopPrice,uv,conversion,collectUserCnt,goodsCtr,userCntAddedBasket,rejectedGoo' \
             'dsCnt,rejectedAmountPct,rejectedAmt,returnedGoodsCnt,returnedAmountPct,returnedAmt,rejectedAndRetur' \
             'nedCnt,rejectedAndReturnedPct,rejectedAndReturnedAmt'

    def __init__(self, account, begin_date, end_date):
        """
        唯品会 档案分析数据 分天查看的表格下载
        :param account:
        :param begin_date:
        :param end_date:
        """
        super(WeipinhuiFile, self).__init__()
        self.__account = account
        self.__begin_date = begin_date
        self.__end_date = end_date

    def crawl_builder(self):
        return CrawlBuilder() \
            .set_url(self.URL) \
            .set_cookies(CookieData.get(CookieData.CONST_PLATFORM_WEIPINHUI, self.__account)) \
            .set_headers_kv('User-Agent', USER_AGENT) \
            .set_get_params_kv('brandStoreName', 'ICY') \
            .set_get_params_kv('brandStoreSn', '10035436') \
            .set_get_params_kv('goodsCode', '') \
            .set_get_params_kv('filter', self.FILTER) \
            .set_get_params_kv('sortColumn', 'bareSalesAmt') \
            .set_get_params_kv('sortType', '1') \
            .set_get_params_kv('pageSize', '20') \
            .set_get_params_kv('pageNumber', '1') \
            .set_get_params_kv('beginDate', self.__begin_date) \
            .set_get_params_kv('endDate', self.__end_date) \
            .set_get_params_kv('brandName', 'ICY女装特卖旗舰店-20191201') \
            .set_get_params_kv('surrogateBrandId', '400462720') \
            .set_get_params_kv('sumType', '1') \
            .set_get_params_kv('optGroupFlag', '0') \
            .set_get_params_kv('warehouseFlag', '0') \
            .set_get_params_kv('analysisType', '0') \
            .set_get_params_kv('selectedGoodsInfo', 'vipshopPrice') \
            .set_get_params_kv('mixBrand', '0') \
            .set_get_params_kv('dateMode', '7') \
            .set_get_params_kv('dateType', 'p') \
            .set_get_params_kv('detailType', 'D') \
            .set_get_params_kv('dailyDate', self.__begin_date) \
            .set_get_params_kv('brandType', '旗舰店') \
            .set_get_params_kv('goodsType', '0') \
            .set_get_params_kv('dateDim', '0') \
            .set_get_params_kv('tagId', '')

    def parse_response(self, response, task):
        headers = response.headers
        if 'Content-Disposition' not in headers or 'attachment' not in headers['Content-Disposition']:
            # 目前这块业务没人管了, 取消报警。
            # processor_logger.error('cookie error')
            # title = '唯品会 档案分析数据 下载文件爬虫报警'
            text = '唯品会 档案分析数据 下载文件爬虫未抓取到 {} 的文件数据，请检查 Mac-Pro 上的 cookie 获取模块'.format(
                self.__begin_date + '|' + self.__end_date)
            # self.crawl_handler_page(DingTalk(ROBOT_TOKEN, title, text))
            return {
                'msg': text,
                'length of content': len(response.content),
            }
        # 写入到 es
        self.save_to_es(response.content)
        account_path = '档案分析/日/档案分析_{begin_date}-{end_date}.xlsx'.format(begin_date=self.__begin_date,
                                                                         end_date=self.__end_date)
        file_path = oss.get_key(oss.CONST_WEIPINHUI_PATH, account_path)
        oss.upload_data(file_path, response.content)
        return {
            'msg': '已获取了唯品会 档案分析数据{}-{}的数据'.format(self.__begin_date, self.__end_date),
            'content length': len(response.content)
        }

    def save_to_es(self, resp):
        """
        把 excel数据 按照指定规则写入es
        :param resp: excel文件 的二进制值内容
        :return:
        """
        excel = ExcelReader(file_contents=resp)
        excel.add_header('goodsCode', '货号') \
            .add_header('goodsName', '商品名称') \
            .add_header('hotType', '热销度') \
            .add_header('logDate', '日期') \
            .add_header('lv3Category', '三级品类类型') \
            .add_header('vipshopPrice', '售卖价') \
            .add_header('onSaleStockAmt', '可售货值') \
            .add_header('onSaleStockCnt', '可售货量') \
            .add_header('userCnt', '客户数') \
            .add_header('goodsActureAmt', '实收金额（含拒退）') \
            .add_header('goodsCnt', '销售量（含拒退）') \
            .add_header('goodsCntWithoutReturn', '销售量（不含拒退）') \
            .add_header('goodsMoney', '销售额（含满减含拒退）') \
            .add_header('goodsAmt', '销售额（扣满减含拒退）') \
            .add_header('goodsAmtWithoutReturn', '销售额(扣满减不含拒退)') \
            .add_header('sellingRatio', '售卖比（销售额）') \
            .add_header('couponAmount', '品牌券金额') \
            .add_header('uv', 'UV')
        excel_list = excel.get_result()
        processor_logger.info('已写入数据到 es')
        if isinstance(excel_list, list) and len(excel_list) > 1:
            Weipinhui().update(excel_list, async=True)
        else:
            # 发报警
            title = '唯品会 档案分析数据 分天查看的表格下载报警'
            text = '唯品会档案分析数据: {} 的es数据写入失败，请检查唯品会的表格是否有字段变动'.format(self.__begin_date)
            self.crawl_handler_page(DingTalk(ROBOT_TOKEN, title, text))

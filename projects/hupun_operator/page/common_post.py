import uuid

from pyspider.helper.excel_reader import ExcelReader
from pyspider.libs.base_crawl import *
from alarm.page.ding_talk import DingTalk
from urllib import parse
from pyspider.helper.excel import Excel
from cookie.model.data import Data as CookieData


class CommonPost(BaseCrawl):
    """
    通用的post请求
    """
    PATH = '/dorado/view-service'
    IMPORT_PURCHASE_RESULT = """{"action":"load-data","dataProvider":"purchaseImportInterceptor#getImpInfo","supportsEntity":true,"resultDataType":"v:purchase.bill$[pchsInfo]","pageSize":0,"pageNo":1,"context":{},"loadedDataTypes":["Catagory","dtStatus","PrintConfig","replenishInfo","MultiOper","dtSearch","dtPurchaseStream","dtException","replenishBill","purchaseBill","dtPostiveNum","pchs_bill_log","GoodsSpec","Currency","dtCondition","dtFractUnit","Region","dtConditionGoods","pchs_detail","Template","dtPchsGoods","Supplier","Oper","Storage","pcshBillBImport","pchsInfo","GoodsPermissions"]}"""
    IMPORT_PURCHASE_ERROR_K = """{"action":"remote-service","service":"excelInterceptor#createExcel","supportsEntity":true,"parameter":{"service":"purchaseImportInterceptor#downloadErrDteail"},"context":{},"loadedDataTypes":["Catagory","dtStatus","PrintConfig","replenishInfo","MultiOper","dtSearch","dtPurchaseStream","dtException","replenishBill","purchaseBill","dtPostiveNum","pchs_bill_log","GoodsSpec","Currency","dtCondition","dtFractUnit","Region","dtConditionGoods","pchs_detail","Template","dtPchsGoods","Supplier","Oper","Storage","pcshBillBImport","pchsInfo","GoodsPermissions"]}"""

    def __init__(self, data, json_result=True):
        super(BaseCrawl, self).__init__()
        self.data = data
        self.json_result = json_result

    def crawl_builder(self):
        return CrawlBuilder() \
            .set_url('{}{}'.format(config.get('hupun', 'service_host'), self.PATH)) \
            .set_task_id(uuid.uuid4()) \
            .set_cookies(CookieData.get(CookieData.CONST_PLATFORM_HUPUN, CookieData.CONST_USER_HUPUN[0][0])) \
            .set_post_data(self.data) \
            .set_headers_kv('Content-Type', 'text/javascript')

    def parse_response(self, response, task):
        if self.json_result:
            return response.json
        return response.text

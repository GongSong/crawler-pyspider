from hupun.page.base import *


class POrderQueResult(Base):
    """
    采购订单 的单条数据查询,从采购订单的搜索栏根据单据编号搜索采购订单
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
   "action":"load-data",
   "dataProvider":"purchaseInterceptor#queryBill",
   "supportsEntity":true,
   "parameter":{
     "billType":0,
     "days":null,
     "startDate":"%s",
     "endDate":"%s",
     "view":"purchase.bill",
     "salemanUids":"",
     "saleman":"",
     "his":false,
     "billCode":"%s"
   },
   "resultDataType":"v:purchase.bill$[purchaseBill]",
   "pageSize":"%d",
   "pageNo":%d,
   "context":{},
   "loadedDataTypes":[
     "Template",
    "replenishInfo",
    "Currency",
    "dtSearch",
    "Storage",
    "Region",
    "Supplier",
    "pchs_bill_log",
    "dtPchsGoods",
    "dtFractUnit",
    "purchaseBill",
    "dtCondition",
    "dtPostiveNum",
    "pchsInfo",
    "dtConditionGoods",
    "Combination",
    "Catagory",
    "pchs_detail",
    "pcshBillBImport",
    "MultiOper",
    "GoodsSpec",
    "Oper",
    "dtException",
    "replenishBill",
    "PrintConfig",
    "dtStatus",
    "dtPurchaseStream",
    "CombinationDetail",
    "GoodsPermissions"
   ]
 }
]]></request>
</batch>
"""
    his_request_data = """
<batch>
<request type="json"><![CDATA[
 {
   "action":"load-data",
   "dataProvider":"purchaseInterceptor#queryBill",
   "supportsEntity":true,
   "parameter":{
     "billType":0,
     "days":"90",
     "startDate":"%s",
     "endDate":"%s",
     "view":"purchase.bill",
     "salemanUids":"",
     "saleman":"",
     "billCode":"%s",
     "his":true
   },
   "resultDataType":"v:purchase.bill$[purchaseBill]",
   "pageSize":"20",
   "pageNo":1,
   "context":{},
   "loadedDataTypes":[
     "dtConditionGoods",
     "dtCondition",
     "pchs_detail",
     "MultiOper",
     "dtPchsGoods",
     "Catagory",
     "replenishBill",
     "purchaseBill",
     "dtStatus",
     "pcshBillBImport",
     "Region",
     "Combination",
     "dtSearch",
     "Storage",
     "GoodsSpec",
     "Currency",
     "Supplier",
     "Oper",
     "dtFractUnit",
     "PrintConfig",
     "replenishInfo",
     "pchsInfo",
     "Template",
     "dtPostiveNum",
     "pchs_bill_log",
     "dtException",
     "dtPurchaseStream",
     "GoodsPermissions",
     "CombinationDetail"
   ]
 }
]]></request>
</batch>
    """

    def __init__(self, bill_code, history=False):
        super(POrderQueResult, self).__init__()
        self.__bill_code = bill_code
        self.__history = history

    def get_request_data(self):
        start_date = Date(self._start_time).to_day_start().format_es_old_utc() if self._start_time else \
            Date.now().to_day_start().format_es_old_utc()
        if self.__history:
            end_date = Date.now().plus_days(-90).format_es_old_utc()
        else:
            end_date = Date(self._end_time).format_es_old_utc() if self._end_time else \
                Date.now().format_es_old_utc()
        return self.his_request_data % (start_date, end_date, self.__bill_code) if self.__history else \
            self.request_data % (start_date, end_date, self.__bill_code, self._page_size, self._page)

    def get_unique_define(self):
        return merge_str('purchase_query_result', self._page, self._page_size, self.__bill_code, self._start_time,
                         self._end_time)

    def parse_response(self, response, task):
        # json 结果
        if 'MessageBox' in response.text:
            print('get hupun result error details: {}'.format(response.text))
            err_msg = response.text.split('MessageBox')[-1] \
                .replace('ERROR_ICON', '').replace('message', '').replace('</exception>', '') \
                .replace('</request>', '').replace('</result>', '').replace(' ', '')
            raise Exception(err_msg)
        result = self.detect_xml_text(response.text)
        return_result = result['data']['data']
        return return_result


if __name__ == '__main__':
    bill_code = 'CD201912240003'
    pur_order_query_obj = POrderQueResult(bill_code) \
        .set_start_time(Date.now().plus_days(-300).format()) \
        .set_cookie_position(1) \
        .get_result()
    print('pur_order_query_obj', pur_order_query_obj)
    # .use_cookie_pool() \

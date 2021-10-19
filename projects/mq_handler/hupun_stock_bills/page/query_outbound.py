from hupun.page.base import *


class QueryOutbound(Base):
    """
    查询 预约出库单 的商品详情
    """
    request_data = """
    <batch>
    <request type="json"><![CDATA[{"action":"load-data","dataProvider":"inventoryInterceptor#queryInoutBill",
    "supportsEntity":true,"parameter":
    {"days":null,
    "startDate":"%s",
    "endDate":"%s","billType":62,
    "remark":"%s","$dataType":"v:inventory.outboundBill$dtSearch"},
    "resultDataType":"v:inventory.outboundBill$[inOutboundBill]","pageSize":20,"pageNo":1,"context":{},"loadedDataTypes":["Storage","Region","inventoryInOutReason","PrintConfig","Combination","dtFractUnit","inOutboundDetail","GoodsSpec","inOutboundBill","Oper","Template","Catagory","locInventory","dtBatchInventory","dtSearch","dtBatch","GoodsPermissions","dtSerialNumber","CombinationDetail"]}]]></request>

    </batch>
    """

    def __init__(self, outbound):
        super(QueryOutbound, self).__init__()
        self.__outbound = outbound

    def get_request_data(self):
        start_date = Date(self._start_time).to_day_start().format_es_old_utc() if self._start_time else \
            Date.now().to_day_start().format_es_old_utc()
        end_date = Date(self._end_time).format_es_old_utc() if self._end_time else \
            Date.now().format_es_old_utc()
        return self.request_data % (start_date, end_date, self.__outbound)

    def get_unique_define(self):
        return merge_str('query_outbound', self.__outbound)

    def parse_response(self, response, task):
        # 爬虫的抓取时间
        sync_time = Date.now().format_es_utc_with_tz()
        # json 结果
        print(response.text)
        result = self.detect_xml_text(response.text).get("data", {}).get("data",[])
        outbound = ""
        if result:
            outbound = result[0].get("stock_code", "")
        return outbound

if __name__ == '__main__':
    QueryOutbound("PH202007300004").set_start_time(Date.now().plus_days(-120).format()).use_cookie_pool().get_result()

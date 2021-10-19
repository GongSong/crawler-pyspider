from hupun.page.base import *
from hupun.model.es.order import Order as EsOrder
from hupun.page.order_goods import OrderGoods


class Order(Base):
    request_data_new = """
<batch><request type="json"><![CDATA[
{
  "action": "load-data",
  "dataProvider": "saleInterceptor#queryTrade",
  "supportsEntity": true,
  "parameter": {
    "view": "sale.query",
    "dateType": 1,
    "buyerType": "1",
    "goodsType": 1,
    "startDate": "%s",
    "startTime": "%s",
    "endDate": "%s",
    "endTime": "%s",
    "history": false,
    "showModify": false,
    "refund": false,
    "detail": 0,
    "containsPackage": false,
    "noSpecContainsPkg": false,
    "unRelated": false,
    "canMerge": false,
    "storage_uid": null,
    "storage_name": "",
    "salemanUid": "",
    "saleman": "",
    "NOSIZE": "true",
    "$dataType": "dtSearch"
  },
  "resultDataType": "v:sale.query$[Trade]",
  "pageSize": "%d",
  "pageNo": %d,
  "context": {},
  "loadedDataTypes": [
    "dtInvoice",
    "Oper",
    "Storage",
    "dtSide",
    "GoodsSpec",
    "MultiOper",
    "PrintConfig",
    "dtMarkType",
    "MultiStorage",
    "operBillType",
    "batchInventory",
    "CombinationGoods",
    "MultiShop",
    "Order",
    "dtQueryCondition",
    "dtStorage",
    "Shop",
    "Template",
    "dtButtonDiy",
    "dtSearchHistory",
    "dtButton",
    "Trade",
    "Region",
    "dtCombination",
    "dtSearch",
    "dtBatch",
    "dtSearchGoods",
    "dtMultiBarcode",
    "GoodsPermissions",
    "dtJzPartner",
    "TradeLog",
    "dtGoodsUniqueCode",
    "dtSerialNumber",
    "dtTradeAddition",
    "dtSalePacking",
    "dtJzPartnerNew"
  ]
}
]]></request></batch>
    """
    request_data_old = """
<batch><request type="json"><![CDATA[
{
  "action": "load-data",
  "dataProvider": "saleInterceptor#queryTrade",
  "supportsEntity": true,
  "parameter": {
    "view": "sale.query",
    "queryIndex": 1,
    "exactType": 1,
    "startDate": "%s",
    "startTime": "%s",
    "endDate": "%s",
    "endTime": "%s",
    "detail": 0,
    "NOSIZE": "true",
    "$dataType": "dtSearchHistory"
  },
  "resultDataType": "v:sale.query$[Trade]",
  "pageSize": "%d",
  "pageNo": %d,
  "context": {},
  "loadedDataTypes": [
    "dtQueryCondition",
    "dtMarkType",
    "Order",
    "dtSearchHistory",
    "dtInvoice",
    "dtButtonDiy",
    "MultiOper",
    "Storage",
    "Oper",
    "MultiShop",
    "dtSearch",
    "Shop",
    "dtCombination",
    "Region",
    "GoodsSpec",
    "dtButton",
    "dtSide",
    "operBillType",
    "MultiStorage",
    "Trade",
    "CombinationGoods",
    "PrintConfig",
    "Template",
    "batchInventory",
    "dtStorage",
    "dtTradeStatement",
    "GoodsPermissions",
    "dtJzPartner",
    "dtMultiBarcode",
    "dtSalePacking",
    "dtSearchGoods",
    "TradeLog",
    "dtGoodsUniqueCode",
    "dtSerialNumber",
    "dtBatch",
    "dtTradeAddition",
    "dtJzPartnerNew"
  ]
}
]]></request></batch>
    """

    def __init__(self, is_old=False, go_next_page=False, catch_details=True, schedule_age=None):
        """
        订单列表爬虫
        :param is_old: 是否老订单（3个月前）
        :param go_next_page: 是否继续下一页
        """
        super(Order, self).__init__()
        # 订单列表失败了就不重复抓了
        self.set_retries(0)
        self.__is_old = is_old
        self.__go_next_page = go_next_page
        self.__catch_details = catch_details
        # schedule_age 只是在抓取订单详情的时候生效，不对订单抓取生效
        self.__schedule_age = schedule_age

    def get_request_data(self):
        """
        返回请求的数据
        他们的时间查询条件实现的比较傻：有4个字段startDate, startTime, endDate, endTime,
        都要传完整的假utc时间，date只用到年月日，time用到时分秒
        :return:
        """
        data = self.request_data_old if self.__is_old else self.request_data_new
        start_time = Date(self._start_time).format_es_old_utc() if self._start_time else Date(
            '2017-01-01').format_es_old_utc()
        end_time = Date(
            self._end_time).format_es_old_utc() if self._end_time else Date.now().to_day_end().format_es_old_utc()
        return data % (
            start_time,
            start_time,
            end_time,
            end_time,
            self._page_size,
            self._page)

    def get_unique_define(self):
        return merge_str(
            'order',
            self._start_time,
            self._end_time,
            self._page_size,
            self._page,
            self.__is_old
        )

    def parse_response(self, response, task):
        sync_time = Date.now().format_es_utc_with_tz()
        try:
            # json可能解析出错，为了不影响后续页面的抓取，继续下发下一页
            result = self.detect_xml_text(response.text)
        except Exception as e:
            self.crawl_next_page()
            raise e
        if len(result['data']['data']):
            for _order in result['data']['data']:
                if _order['tp_type'] == 50 and not _order['tp_tid']:
                    _order['tp_tid'] = _order['salercpt_no']
                # 过滤掉万里牛的页面接口已经抓不到的字段
                filter_words = ['tp_buyer', 'tp_receiver_mobile', 'tp_receiver_address', 'tp_receiver_name',
                                'show_buyer']
                for word in filter_words:
                    if word in _order.keys():
                        if not _order.get(word):
                            _order.pop(word)

                _order['tp_tids'] = _order['tp_tid'].split('|') if _order['tp_tid'] else []
                _order['sync_time'] = sync_time
                # 取消保存数据到mongo
                # self.send_message(_order, merge_str('order', _order.get('salercpt_uid', '')))
                if self.__catch_details:
                    self.crawl_handler_page(
                        OrderGoods(_order['salercpt_uid'], _order['storage_uid'], _order['tp_tid'],
                                   _order['trade_create_time'], self.__is_old)
                            .set_age(self.__schedule_age)
                            .use_cookie_pool(self._use_cookie_pool)
                    )
            EsOrder().update(result['data']['data'], async=True)
            self.crawl_next_page()
        return {
            # 'text': response.text,
            'start_time': self._start_time,
            'end_time': self._end_time,
            'page': self._page,
            'page_size': self._page_size,
            'priority': self._priority,
            'is_old': self.__is_old,
        }

    def crawl_next_page(self):
        """
        爬下一页
        :return:
        """
        if self.__go_next_page and not self.check_flag(self.CONST_FLAG_BREAK) and self.in_processor():
            Order(self.__is_old, self.__go_next_page) \
                .set_start_time(self._start_time) \
                .set_end_time(self._end_time) \
                .set_page(self._page + 1) \
                .set_page_size(self._page_size) \
                .set_priority(self._priority) \
                .use_cookie_pool(self._use_cookie_pool) \
                .enqueue()  # 有可能解析错误，报异常, 也要强制入队

    @staticmethod
    def run_days(start, end, priority=0):
        """
        更新指定时间区间的数据
        :param priority:
        :param start:
        :param end:
        :return:
        """
        for _ in Date.generator_date(start, end):
            Order(go_next_page=True) \
                .set_start_time(_.to_day_start().format()) \
                .set_end_time(_.to_day_end().format()) \
                .set_priority(priority) \
                .enqueue()

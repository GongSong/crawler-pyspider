import uuid

from hupun.model.es.goods_information import GoodsInformationEs as GoodsInforEs
from hupun.page.base import *
from hupun.page.hupun_goods.goods_information_sku import GoodsInformationsku


class GoodsInformation(Base):
    """
    万里牛 商品信息 的数据
    """
    request_data = """
<batch>
<request type="json"><![CDATA[
 {
   "action":"load-data",
   "dataProvider":"goodsInterceptor#queryGoods",
   "supportsEntity":false,
   "parameter":{
     "orderColumn":"goods_code",
     "orderSeq":"asc",
     "needCata":true,
     "status":"%d",
     "brands":"",
     "brandNames":"-- 所有品牌 --",
     "$dataType":"v:goods.Goods$dtSearch"
   },
   "resultDataType":"v:goods.Goods$[Goods]",
   "pageSize":"%d",
   "pageNo":%d,
   "context":{}
 }
]]></request>
</batch>
"""
    # 状态，1 为启用中
    status = 1

    def __init__(self, go_next_page=False):
        super(GoodsInformation, self).__init__()
        self.__go_next_page = go_next_page

    def get_request_data(self):
        return self.request_data % (self.status, self._page_size, self._page)

    def get_unique_define(self):
        return merge_str('goods_information', uuid.uuid4())

    def parse_response(self, response, task):
        # 爬虫的抓取时间
        sync_time = Date.now().format_es_utc_with_tz()
        # json 结果
        result = self.detect_xml_text(response.text)
        if len(result['data']['data']):
            for _item in result['data']['data']:
                goods_uid = _item['goodsUid']
                _item['sync_time'] = sync_time
                self.crawl_handler_page(
                    GoodsInformationsku(goods_uid).set_priority(GoodsInformationsku.CONST_PRIORITY_BUNDLED))
            # 抓取下一页
            self.crawl_next_page()
            # 这个异步更新数据需要开启 es 队列去消费
            GoodsInforEs().update(result['data']['data'], async=True)
        return {
            'tag': '万里牛的商品信息数据',
            'length': len(response.content),
            # 'response': response.text,
        }

    def crawl_next_page(self):
        """
        爬下一页
        :return:
        """
        if self.__go_next_page:
            self.crawl_handler_page(
                GoodsInformation(go_next_page=self.__go_next_page)
                    .set_page(self._page + 1)
                    .set_page_size(self._page_size)
                    .set_priority(self._priority)
            )

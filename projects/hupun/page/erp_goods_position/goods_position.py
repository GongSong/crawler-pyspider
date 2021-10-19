import re
import traceback
from hupun.page.base import *
from pyspider.core.model.storage import ai_storage_redis


class GoodsPosition(Base):
    """
    获取请求的token值
    """
    request_data = """
    <batch>
    <request type="json"><![CDATA[{"action":"load-data","dataProvider":"storageLocInterceptor#queryStorageLoc","supportsEntity":true,
    "parameter":{"storage_uid":"D1E338D6015630E3AFF2440F3CBBAFAD","storage_name":"总仓",
    "spec_code":null,"goods_uid":null,"spec_uid":null,"uid1":null,"uid2":null,"uid3":null,"uid4":null},
    "resultDataType":"v:basic.StorageLoc$[StorageLoc]","pageSize": %d,"pageNo":%d,"context":{},
    "loadedDataTypes":["StorageLocBatch","StorageLoc","Combination","Catagory","dtImportType","dtCondition","StorageShelf","Storage","Template","PrintConfig","dtLocInventory","GoodsSpec","CombinationDetail","GoodsPermissions"]}]]></request>
    </batch>
    """

    def __init__(self, page=1):
        super(GoodsPosition, self).__init__()
        self._page = page
        self._page_size = 20
        self.__break = False

    def get_request_data(self):
        return self.request_data % (self._page_size, self._page)

    def get_unique_define(self):
        now_timestamp = Date.now().millisecond()
        return merge_str('appointment_sku_info', now_timestamp)

    def parse_response(self, response, task):
        # json 结果
        try:
            result = self.detect_xml_text(response.text)

            # 库位号优先拿B区
            priority_area = ["b", "B"]
            page_total = result.get("data", {}).get("pageCount", 1)
            reuslt_list = result.get("data", {}).get("data", [])
            for i in reuslt_list:
                sku_list = i.get("goods", "")
                position = i.get("location_code","")
                if sku_list:
                    skus = sku_list.split("]，")
                    for k in skus:
                        s = "hupun:location:" + re.findall("商品：(.*?)，数量", k)[0]
                        origin_position = ai_storage_redis.get(s)
                        if isinstance(origin_position, str) and len(origin_position) > 0 and origin_position[0] in priority_area:
                            ai_storage_redis.set(s, origin_position, ex=3600*24)
                            continue
                        ai_storage_redis.set(s, position, ex=3600*24)

            # 可能返回空值
            return reuslt_list, page_total
        except Exception as e:
            print(response.text)
            print(traceback.format_exc())
            return


if __name__ == '__main__':
    current_page = 1
    total_page = 1
    try:
        while current_page <= total_page:
            print(current_page)
            res = GoodsPosition(current_page).use_cookie_pool().get_result()
            time.sleep(1)
            current_page += 1
            total_page = res[1]
    except Exception as e:
        title = '更新总仓货位信息程序警告'
        msg = "更新总仓货位信息失败，{}".format(e)

        print(msg)

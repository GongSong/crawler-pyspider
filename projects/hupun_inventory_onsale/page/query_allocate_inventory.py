from hupun.page.base import *
import traceback


class QueryAllocateInventory(Base):
    """
    库存订单同步例外宝贝设置中，更改自动上架开关的状态
    """

    request_data = """
    <batch>
    <request type="json"><![CDATA[
    {"action":"load-data","dataProvider":"inventoryInterceptor#queryInventoryChangeBill","supportsEntity":true,"parameter":{
    "days":"7","startDate":"%s","endDate":"%s","bill_type":4,
    "view":"inventory.transferNew","his":false,
    "code":"%s",
    "$dataType":"v:inventory.transferNew$dtSearch"},
    "resultDataType":"v:inventory.transferNew$[dtTransferBill]","pageSize":20,"pageNo":1,"context":{},"loadedDataTypes":
    ["PrintConfig","dtTransferDetail","Template","Custom","dtSearch","dtFractUnit",
    "Combination","Storage","Catagory","dtExpGoods","dtTransferBill","Oper","GoodsSpec","GoodsPermissions","CombinationDetail"]}
    ]]></request>
    </batch>
        """

    def __init__(self, inv_change_code):
        # target_status为1时，关闭【自动上架】。为2时，开启【自动上架】。
        super(QueryAllocateInventory, self).__init__()
        self.__inv_change_uid = inv_change_code

    def get_request_data(self):
        # 默认搜索360天内的调拨单
        start_date = Date(self._start_time).format_es_old_utc() if self._start_time else \
            Date.now().plus_days(-360).format()
        end_date = Date(self._end_time).format_es_old_utc() if self._end_time else \
            Date.now().format_es_old_utc()
        return self.request_data % (start_date, end_date, self.__inv_change_uid)

    def get_unique_define(self):
        return merge_str('check_allocate_inventory', self.__inv_change_uid)

    def parse_response(self, response, task):
        try:
            if '会话过期' in response.text:
                return False, '查询库存调拨单时会话过期'
            if '单据不存在' in response.text:
                return 'rate', '查询库存调拨单时单据不存在'
            elif '库存更新过于繁忙' in response.text:
                return 'rate', '库存更新过于繁忙'
            elif '单据已经被其他人操作' in response.text:
                return 'other', '查询库存调拨单时单据已经被其他人操作'
            else:
                result = self.detect_xml_text(response.text)
                bill = result.get('data', {}).get('data', [])
                if len(bill) == 1:
                    inv_change_uid = bill[0].get('inv_change_uid', '')
                    return True, inv_change_uid
                else:
                    return 'rate', '查询库存调拨单时，未找到该订单'
        except Exception as e:
            print(traceback.format_exc())
            return 'other', '查询库存调拨单时发生未被捕捉到的异常'


if __name__ == '__main__':
    # 根据cookie确定审核员的名字
    print(QueryAllocateInventory('DB201808310014').set_cookie_position(3).get_result())

from hupun_operator.page.warehouse.create_storage import CreateStorage
from hupun_operator.page.warehouse.query_storage import QueryStorage
from hupun_operator.page.warehouse.update_storage import UpdateStorage
from mq_handler.base import Base
from pyspider.helper.crawler_utils import CrawlerHelper
from alarm.page.ding_talk import DingTalk
from cookie.config import ROBOT_TOKEN


class SyncErpWarehouse(Base):
    """
    同步 erp仓库的数据
    TODO - 未做并发数据检查
    """

    def execute(self):
        print('同步erp仓库的数据')
        self.print_basic_info()
        storage_list_obj = QueryStorage(self._data.get("erpWarehouseNo")).use_cookie_pool()
        storage_status, storage_list_result = CrawlerHelper.get_sync_result(storage_list_obj)
        if storage_status == 1:
            assert False, '爬虫获取仓库同步list失败:{}'.format(storage_list_result)
        warehouse_list = storage_list_result["data"]
        is_new = True
        storage_uid = ""
        com_uid = ""
        if len(warehouse_list) != 0:
            for warehouse in warehouse_list:
                if warehouse.get("storageCode") == self._data.get("erpWarehouseNo"):
                    is_new = False
                    storage_uid = warehouse.get("storageUid")
                    com_uid = warehouse.get("comUid")
                    break
        if not is_new:
            update_obj = UpdateStorage(self._data, storage_uid, com_uid).use_cookie_pool()
            update_status, update_result = CrawlerHelper.get_sync_result(update_obj)
            print(update_result)
            if update_status == 1:
                title = '爬虫仓库更新失败报警'
                text = '爬虫仓库更新失败: {} '.format(update_result)
                DingTalk(ROBOT_TOKEN, title, text).enqueue()
                assert False, '爬虫仓库更新失败:{}'.format(update_result)
            return

        create_obj = CreateStorage(self._data).use_cookie_pool()
        create_status, create_result = CrawlerHelper.get_sync_result(create_obj)
        print(create_result)
        if create_status == 1:
            title = '爬虫创建仓库失败报警'
            text = '爬虫创建仓库失败: '.format(create_result)
            DingTalk(ROBOT_TOKEN, title, text).enqueue()
            assert False, '爬虫创建仓库失败:{}'.format(create_result)

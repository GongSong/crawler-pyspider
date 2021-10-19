import json
from alarm.page.ding_talk import DingTalk
from landong.config import WARNING_DELAY_TIME, LANDONG_ROBOT_TOKEN
from landong.model.es.bas_product_category import BasProductCategoryEs
from landong.page.inform.bas_pattern_category import BasPatternCategoryInform
from landong.page.inform.bas_pattern_size_inform import BasPatternSizeInform
from pyspider.helper.date import Date
from landong.model.es.bas_pattern_size import BasPatternSizeEs
from pyspider.libs.base_crawl import *
from weipinhui_migrate.config import *
from landong.page.base import Base


class BaiDu(Base):
    PATH = "http://www.baidu.com/"

    def __init__(self, type_corn=None):
        """
        访问百度，定时推送不重复的尺码和品类档案
        """
        super(BaiDu, self).__init__()
        self.type_corn = type_corn

    def get_unique_define(self):
        return ":".join([self.PATH, self.type_corn, str(Date().now().timestamp())])

    def crawl_builder(self):
        return CrawlBuilder() \
            .set_url(self.PATH + "#{}".format(self.get_unique_define())) \
            .set_headers_kv('User-Agent', USER_AGENT)

    def parse_response(self, response, task):
        if self.type_corn == "size":
            send_data = self.size_corn()
        else:
            send_data = self.category_corn()
        sync_time = Date.now().format_es_utc_with_tz()
        return {
            'send_data': send_data,
            'sync_time': sync_time,
        }

    def size_corn(self):
        """
        定时更新澜东云尺码档案数据
        """
        size_keys_data = default_storage_redis.keys("size:*")
        update_size_data = []
        update_data = []
        send_data = []
        code_name_list = []
        for key in size_keys_data:
            size_data = json.loads(default_storage_redis.get(key))
            update_size_data.append(size_data)
            code_name_list.append(size_data.get("DataCode", ""))
            code_name_list.append(size_data.get("DataName", ""))
        if len(code_name_list) > 0:
            repeat_list, only_list = find_repeat_data(code_name_list)
            for item in update_size_data:
                if item.get("DataCode") in repeat_list or item.get("DataName") in repeat_list:
                    title = "澜东云-尺码档案-有冗余数据"
                    text = "冗余数据: {}".format(item)
                    send_ding_talk(title, text, item.get("DataCode"))
                else:
                    update_data.append(item)
        if len(update_data) > 0:
            for item in update_data:
                default_storage_redis.delete("size:" + item.get("UUID"))
                send_data.append(
                    {
                        "name": item.get("DataName", ""),
                        "code": item.get("DataCode", ""),
                        # 尺码组
                        "sizeGroup": item.get("PatternSizeGroupName", ""),
                        "status": 1 if item.get("Enabled", True) else 0
                    }
                )
            BasPatternSizeEs().update(update_data)
            self.crawl_handler_page(BasPatternSizeInform(send_data))
        return send_data

    def category_corn(self):
        """
        定时更新澜东云品类档案数据
        """
        category_keys_data = default_storage_redis.keys("category:*")
        update_category_data = []
        update_data = []
        send_data = []
        code_name_list = []
        # 款号取值判重list
        data_value_list = []

        # 所有品类档案的map数据
        data_map = {}
        # 把redis和es的数据做交集，以redis的数据为准
        es_data_map = BasProductCategoryEs().get_category_code_map()
        for key in category_keys_data:
            data = json.loads(default_storage_redis.get(key))
            data_map.setdefault(data.get("UUID"), data.get("CategoryCode"))

            code = data.get("CategoryCode", "")
            name = data.get("CategoryName", "")

            data_value = data.get("DataValue", "")
            if data_value:
                # DataValue - 款号取值不能超过两位，不能重复，可以为空
                if len(data_value) > 2:
                    title = "澜东云-品类档案-款号取值超过了两位"
                    text = "品类编码: {},品类名称: {} 的款号取值:{} 超过了两位".format(code, name, data_value)
                    send_ding_talk(title, text, code + "toolong")
                    continue
                elif data_value in data_value_list:
                    title = "澜东云-品类档案-款号取值不能重复"
                    text = "品类编码: {},品类名称: {} 的款号取值:{} 不能重复".format(code, name, data_value)
                    send_ding_talk(title, text, code + "repeated")
                    continue
                data_value_list.append(data_value)

            update_category_data.append(data)
            code_name_list.append(code)
            code_name_list.append(name)

            if data.get("UUID", "") in es_data_map:
                es_data_map.pop(data.get("UUID", ""))
        data_map.update(es_data_map)

        if len(code_name_list) > 0:
            repeat_list, only_list = find_repeat_data(code_name_list)
            for item in update_category_data:
                if item.get("CategoryCode") in repeat_list or item.get("CategoryName") in repeat_list:
                    title = "澜东云-品类档案-有冗余数据"
                    text = "冗余数据: {}".format(item)
                    send_ding_talk(title, text, item.get("CategoryCode"))
                else:
                    update_data.append(item)
        if len(update_data) > 0:
            for item in update_data:
                default_storage_redis.delete("category:" + item.get("UUID"))
                parent_id = item.get("ParentId")
                if parent_id is None:
                    parent_code = ""
                else:
                    parent_code = data_map.get(parent_id)
                send_data.append(
                    {
                        "name": item.get("CategoryName", ""),
                        "code": item.get("CategoryCode", ""),
                        "status": 1 if item.get("Enabled", True) else 0,
                        "parentCode": parent_code,
                        "value": item.get("DataValue", ""),
                    }
                )
            BasProductCategoryEs().update(update_data)
            self.crawl_handler_page(BasPatternCategoryInform(send_data))
        return send_data


def find_repeat_data(name_list):
    """
    查找列表中重复的数据
    :param name_list:
    :return: 一个重复数据的列表，列表中字典的key 是重复的数据，value 是重复的次数
    """
    repeat_list = []
    only_list = []
    for i in set(name_list):
        ret = name_list.count(i)  # 查找该数据在原列表中的个数
        if ret > 1:
            repeat_list.append(i)
        else:
            only_list.append(i)
    return repeat_list, only_list


def send_ding_talk(title, content, unique_key):
    """
    发送钉钉报警
    :param title: 报警标题
    :param content: 报警内容
    :param unique_key: 本次报警的唯一标识
    :return:
    """
    if not default_storage_redis.get(unique_key):
        default_storage_redis.set(unique_key, "1", WARNING_DELAY_TIME)
        DingTalk(LANDONG_ROBOT_TOKEN, title, content).enqueue()

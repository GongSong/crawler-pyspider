import json
from landong.model.es.bas_pattern_size import BasPatternSizeEs
from landong.page.base import Base
from landong.page.corn.corn import send_ding_talk
from pyspider.helper.date import Date
from pyspider.core.model.storage import default_storage_redis


class BasPatternSize(Base):
    """
    澜东 尺码档案
    """

    PATH = "/Bas/PatternSize/PagedQueryByGroupId"

    def __init__(self, node, next_page=False):
        super(BasPatternSize, self).__init__()
        self.next_page = next_page
        self.node = node

    def get_api_route(self):
        return self.PATH

    def get_unique_define(self):
        return self.node

    def get_post_data(self):
        return {
            "filter": "",
            "nodeId": self.node,
            "page": self._page,
            "start": (self._page - 1) * self._limit if self._page > 0 else 0,
            "limit": self._limit,
        }

    def parse_response(self, response, task):
        """
        解析相应数据
        """
        content = response.json
        data = content.get("data", [])
        total = content.get("total", 0)

        # 尺码档案如果有新增或者更新，就存储redis
        self.data_to_redis(data)
        sync_time = Date.now().format_es_utc_with_tz()

        if self.next_page and total > self._limit * self._page:
            self.crawl_handler_page(BasPatternSize(self.next_page).set_page(self._page + 1))
        return {
            "response": response.text[:200],
            "sync_time": sync_time,
        }

    def data_to_redis(self, data):
        """
        若有更新或者变动, 存储redis
        """
        # 存储到redis的数据
        redis_data = []

        size_data = BasPatternSizeEs().get_all_pattern_size()
        size_code_data, size_name_data = BasPatternSizeEs().get_all_size()

        # 名称主键，UUID值
        name_uuid_map = {}
        # 编码主键，UUID值
        code_uuid_map = {}
        for _ in size_data.keys():
            name_uuid_map.setdefault(size_data.get(_, {}).get("DataName", ""), _)
            code_uuid_map.setdefault(size_data.get(_, {}).get("DataCode", ""), _)

        # 判断尺码档案是否有更新
        for item in data:
            uuid = item.get("UUID", "")
            name = item.get("DataName", "")
            code = item.get("DataCode", "")
            if len(code) > 2:
                # DataCode 尺码编码，长度不能超过两位，否则报警
                title = "澜东云-尺码档案-尺码编码长度超过两位"
                text = "尺码编码: {}, 尺码名称: {}, 长度超过两位".format(code, name)
                send_ding_talk(title, text, code)
                continue

            group_name = item.get("PatternSizeGroupName", "")
            update_time = item.get("UpdateOn")

            size = size_data.get(uuid)

            if size is None:
                # 新增
                if name in size_name_data or code in size_code_data:
                    title = "澜东云-尺码档案-新增尺码，产生重复尺码"
                    text = "新增尺码的尺码组: {}, 尺码编码: {},尺码名称: {}".format(group_name, code, name)
                    send_ding_talk(title, text, code)
                    continue
                else:
                    redis_data.append(item)
                    default_storage_redis.set("size:" + uuid, json.dumps(item), ex=3600)
            else:
                # 更新
                size_update_time = size.get("UpdateOn")
                if update_time:
                    if "." in update_time:
                        update_time = update_time.split(".")[0]
                    if not size_update_time:
                        if (name in size_name_data and uuid != name_uuid_map.get(name, "")) or (
                                code in size_code_data and uuid != code_uuid_map.get(code, "")):
                            title = "澜东云-尺码档案-更新尺码，产生重复尺码"
                            text = "更新尺码的尺码组: {}, 尺码编码: {},尺码名称: {}".format(group_name, code, name)
                            send_ding_talk(title, text, code)
                            continue
                        else:
                            redis_data.append(item)
                            default_storage_redis.set("size:" + uuid, json.dumps(item), ex=3600)
                    else:
                        if "." in size_update_time:
                            size_update_time = size_update_time.split(".")[0]
                        if Date(update_time).millisecond() > Date(size_update_time).millisecond():
                            if (name in size_name_data and uuid != name_uuid_map.get(name)) or (
                                    code in size_code_data and uuid != code_uuid_map.get(code)):
                                title = "澜东云-尺码档案-新增尺码，产生重复尺码"
                                text = "新增尺码的尺码组: {}, 尺码编码: {},尺码名称: {}".format(group_name, code, name)
                                send_ding_talk(title, text, code)
                                continue
                            else:
                                redis_data.append(item)
                                default_storage_redis.set("size:" + uuid, json.dumps(item), ex=3600)

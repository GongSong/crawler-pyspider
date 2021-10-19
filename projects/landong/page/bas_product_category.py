import json

from landong.model.es.bas_product_category import BasProductCategoryEs
from landong.page.base import Base
from landong.page.corn.corn import send_ding_talk, BaiDu
from pyspider.helper.date import Date
from pyspider.core.model.storage import default_storage_redis


class BasProductCategory(Base):
    PATH = "/Bas/ProductCategory/PagedQuery"

    def __init__(self, next_page=False):
        """
        品类档案
        """
        super(BasProductCategory, self).__init__()
        self.next_page = next_page

    def get_api_route(self):
        return self.PATH

    def get_unique_define(self):
        return ":".join([self.PATH, str(self._page), str(Date().now().timestamp())])

    def get_post_data(self):
        return {
            "filter": "",
            "page": self._page,
            "start": (self._page - 1) * self._limit if self._page > 0 else 0,
            "limit": self._limit,
        }

    def parse_response(self, response, task):
        """
        解析响应数据
        """
        content = response.json
        data = content.get("data", [])
        total = content.get("total", 0)

        self.data_to_redis(data)

        sync_time = Date().now().format_es_utc_with_tz()

        if self.next_page and total > self._limit * self._page:
            self.crawl_handler_page(BasProductCategory(self.next_page).set_page(self._page + 1))
        else:
            # 把澜东云品类数据从redis更新到ES
            self.crawl_handler_page(BaiDu(type_corn="category"))

        return {
            "response": response.text[:200],
            "sync_time": sync_time,
        }

    def data_to_redis(self, data):
        """
        品类新增或者更新时，存储redis
        """
        # 存储到redis的数据
        redis_data = []

        category_data = BasProductCategoryEs().get_all_pattern_category()
        category_code_data, category_name_data = BasProductCategoryEs().get_all_category()

        # 名称主键，UUID值
        name_uuid_map = {}
        # 编码主键，UUID值
        code_uuid_map = {}
        for _ in category_data.keys():
            name_uuid_map.setdefault(category_data.get(_, {}).get("CategoryName", ""), _)
            code_uuid_map.setdefault(category_data.get(_, {}).get("CategoryCode", ""), _)

        for item in data:
            uuid = item.get("UUID")
            code = item.get("CategoryCode")
            name = item.get("CategoryName")
            update_time = item.get("UpdateOn")

            pattern_category_map = category_data.get(uuid)

            if pattern_category_map is None:
                # 新增
                if name in category_name_data or code in category_code_data:
                    title = "澜东云-品类档案-新增品类，产生重复品类"
                    text = "新增品类编码: {},品类名称: {}".format(code, name)
                    send_ding_talk(title, text, code)
                    continue
                else:
                    redis_data.append(item)
                    default_storage_redis.set("category:" + uuid, json.dumps(item), ex=3600)
            else:
                # 更新
                category_update_time = pattern_category_map.get("UpdateOn")
                if update_time:
                    if "." in update_time:
                        update_time = update_time.split(".")[0]
                    if not category_update_time:
                        if (name in category_name_data and uuid != name_uuid_map.get(
                                name)) or (code in category_code_data and uuid != code_uuid_map.get(code)):
                            title = "澜东云-品类档案-更新品类，产生重复品类"
                            text = "更新品类编码: {},品类名称: {}".format(code, name)
                            send_ding_talk(title, text, code)
                            continue
                        else:
                            redis_data.append(item)
                            default_storage_redis.set("category:" + uuid, json.dumps(item), ex=3600)
                    else:
                        if "." in category_update_time:
                            category_update_time = category_update_time.split(".")[0]
                        if Date(update_time).millisecond() > Date(category_update_time).millisecond():
                            if (name in category_name_data and uuid != name_uuid_map.get(
                                    name)) or (code in category_code_data and uuid != code_uuid_map.get(code)):
                                title = "澜东云-品类档案-更新品类，产生重复品类"
                                text = "更新品类编码: {},品类名称: {}".format(code, name)
                                send_ding_talk(title, text, code)
                                continue
                            else:
                                redis_data.append(item)
                                default_storage_redis.set("category:" + uuid, json.dumps(item), ex=3600)

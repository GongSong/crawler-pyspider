from landong.model.es.bas_brand import BasBrandEs
from landong.page.base import Base
from landong.page.inform.bas_brand_inform import BasBrandInform
from pyspider.helper.date import Date


class BaseBrand(Base):
    """
    波段档案
    """

    PATH = "/Bas/Band/PagedQuery"

    def __init__(self, next_page=False):
        super(BaseBrand, self).__init__()
        self.next_page = next_page

    def get_post_data(self):
        data = {
            "page": self._page,
            "limit": self._limit,
            "start": (self._page - 1) * self._limit if self._page > 0 else 0,
        }
        return data

    def get_api_route(self):
        return self.PATH

    def get_unique_define(self):
        return ":".join([self.PATH, str(self._page), str(Date().now().timestamp())])

    def parse_response(self, response, task):
        content = response.json
        data = content.get("data", [])
        total = content.get("total", 0)

        # 波段档案如果有新增或者更新，就通知给天鸽
        self.inform_to_tg(data)

        sync_time = Date.now().format_es_utc_with_tz()
        for item in data:
            item["sync_time"] = sync_time
        BasBrandEs().update(data, async=True)

        # 抓取下一页
        if self.next_page and total > self._limit * self._page:
            self.crawl_handler_page(BaseBrand(self.next_page).set_page(self._page + 1))

        # 解析响应
        return {
            "response": response.text[:200],
            "sync_time": sync_time
        }

    def inform_to_tg(self, data):
        """
        波段档案如果有新增或者更新，就通知给天鸽
        :param data:
        """
        # 把数据保存到内存
        bas_brands_map = {}
        all_bas_brand = BasBrandEs().get_all_bas_brand()
        for bas_brand_list in all_bas_brand:
            for bas in bas_brand_list:
                bas_brands_map.setdefault(bas.get("UUID", "none-1"), bas)

        # 判断数据是否是新增或更新的
        for item in data:
            uuid = item.get("UUID", "")
            code = item.get("DataCode", "")
            name = item.get("DataName", "")
            status = 1 if item.get("Enabled", False) else 0
            creator = item.get("CreateByName", "")
            create_time = item.get("CreateOn")
            update_time = item.get("UpdateOn")

            origin_bas_brand = bas_brands_map.get(uuid)
            if origin_bas_brand is None:
                # 新增
                self.crawl_handler_page(BasBrandInform(code, name, status, creator, create_time))
            else:
                # 更新
                origin_update_time = origin_bas_brand.get("UpdateOn")
                if update_time:
                    if "." in update_time:
                        update_time = update_time.split(".", 1)[0]
                    if not origin_update_time:
                        self.crawl_handler_page(BasBrandInform(code, name, status, creator, create_time))
                    else:
                        if "." in origin_update_time:
                            origin_update_time = origin_update_time.split(".", 1)[0]
                        if Date(update_time) > Date(origin_update_time):
                            self.crawl_handler_page(BasBrandInform(code, name, status, creator, create_time))

from alarm.page.ding_talk import DingTalk
from landong.config import LANDONG_ROBOT_TOKEN, WARNING_DELAY_TIME
from landong.model.es.bas_product_color import BasProductColorEs
from landong.page.base import Base
from landong.page.inform.bas_product_color_inform import BasProductColorInform
from pyspider.core.model.storage import default_storage_redis
from pyspider.helper.date import Date


class BaseProductColor(Base):
    """
    颜色档案
    """

    PATH = "/Bas/ProductColor/PagedQuery"
    COLOR_NUM_LIMIT = 9

    def __init__(self, next_page=False):
        super(BaseProductColor, self).__init__()
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

        # 颜色档案如果有新增或者更新，就通知给天鸽
        try:
            save_data = self.inform_to_tg(data)
        except Exception as e:
            err_msg = "颜色档案 的抓取发生异常:{}".format(e.args)
            self.send_ding_talk(err_msg, Date.now().timestamp())
            raise Exception(err_msg)

        sync_time = Date.now().format_es_utc_with_tz()
        for item in save_data:
            item["sync_time"] = sync_time
        BasProductColorEs().update(save_data, async=True)

        # 抓取下一页
        if self.next_page and total > self._limit * self._page:
            self.crawl_handler_page(BaseProductColor(self.next_page).set_page(self._page + 1))

        # 解析响应
        return {
            "response": response.text[:200],
            "sync_time": sync_time
        }

    def inform_to_tg(self, data):
        """
        颜色档案 如果有新增或者更新，就通知给天鸽
        :param data:
        """
        # 返回非重复的数据，用于写入es
        return_data = []
        # 用 颜色编码、颜色名称和颜色的uuid 判断数据是否重复
        code_list = []
        name_list = []
        uuid_list = []
        # 把数据保存到内存
        origin_bas_color_map = {}
        bas_color_map = {}
        all_bas_colors = BasProductColorEs().get_all_bas_color()
        for bas_color_list in all_bas_colors:
            for bas in bas_color_list:
                origin_bas_color_map.setdefault(bas.get("UUID", "none-1"), bas)
                code_list.append(bas.get("ColorCode", ""))
                name_list.append(bas.get("ColorName", ""))
                uuid_list.append(bas.get("UUID", "none-1"))

        # 用 颜色编码、颜色名称 判断本次抓取的数据是否重复
        now_code_list = []
        now_name_list = []

        # 判断数据是否是新增或更新的
        for item in data:
            uuid = item.get("UUID", "")
            color_base_name = item.get("ColorBaseName", "")  # 颜色分类
            color_name = item.get("ColorName", "")  # 颜色名称
            color_code = item.get("ColorCode", "")  # 颜色编码

            # 颜色编码只能有2位，由一个字母和一个0-9之间的数据组成
            if len(color_code) > 2:
                err_msg = "颜色编码:【{}】的格式不对，长度超过了2位".format(color_code)
                self.send_ding_talk(err_msg, color_name)
                continue

            initials_code = color_code[:1]  # 澜东颜色编码首字母（如J01中的J）
            num_initials_code = int(color_code[1:])  # 澜东颜色编码中的数字（如J01中的1）（注意，不是01）
            rgb_hex = "#" + item.get("RgbHex", "")  # 16进制颜色值（#C9C9C9）（大写带#号）
            status = 1 if item.get("Enabled", False) else 0  # 0停用 1启用
            update_time = item.get("UpdateOn")

            # 重复的颜色就报警
            if (color_name in name_list and uuid not in uuid_list) or color_name in now_name_list:
                err_msg = "颜色名:【{}】重复了".format(color_name)
                self.send_ding_talk(err_msg, color_name)
                continue
            if (color_code in code_list and uuid not in uuid_list) or color_code in now_code_list:
                err_msg = "颜色编码:【{}】重复了".format(color_code)
                self.send_ding_talk(err_msg, color_code)
                continue

            # 单个颜色目前页面上限是10个子颜色
            # 超过10个子颜色爬虫报警
            if num_initials_code > self.COLOR_NUM_LIMIT:
                err_msg = "颜色:【{}】的子颜色数量超过:{} 个".format(color_name, self.COLOR_NUM_LIMIT)
                unique_key = uuid if uuid else "1"
                self.send_ding_talk(err_msg, unique_key)
                continue

            return_data.append(item)
            now_name_list.append(color_name)
            now_code_list.append(color_code)

            origin_bas_brand = origin_bas_color_map.get(uuid)
            if origin_bas_brand is None:
                # 新增
                self.save_color_map(bas_color_map, initials_code, color_base_name, num_initials_code, color_name,
                                    status, rgb_hex)
            else:
                # 更新
                origin_update_time = origin_bas_brand.get("UpdateOn")
                if update_time:
                    if "." in update_time:
                        update_time = update_time.split(".", 1)[0]
                    if not origin_update_time:
                        self.save_color_map(bas_color_map, initials_code, color_base_name, num_initials_code,
                                            color_name, status, rgb_hex)
                    else:
                        if "." in origin_update_time:
                            origin_update_time = origin_update_time.split(".", 1)[0]
                        if Date(update_time) > Date(origin_update_time):
                            self.save_color_map(bas_color_map, initials_code, color_base_name, num_initials_code,
                                                color_name, status, rgb_hex)
        if len(bas_color_map) > 0:
            post_data = {
                "list": [v for k, v in bas_color_map.items()]
            }
            self.crawl_handler_page(BasProductColorInform(post_data))

        return return_data

    def save_color_map(self, bas_color_map: dict, initials_code, color_base_name, num_initials_code, color_name, status,
                       rgb_hex):
        """
        把颜色信息保存到map里

        :param bas_color_map:
        :param initials_code:
        :param color_base_name:
        :param num_initials_code:
        :param color_name:
        :param status:
        :param rgb_hex:
        :return:
        """
        if bas_color_map.get(initials_code):
            sub_item = bas_color_map.get(initials_code, {}).get("subColorList", [])
            sub_item.append({
                "code": num_initials_code,
                "name": color_name,
                "status": status,
                "value": rgb_hex,
            })
        else:
            bas_color_map.setdefault(initials_code, {
                "name": color_base_name,
                "code": initials_code,
                "subColorList": [{
                    "code": num_initials_code,
                    "name": color_name,
                    "status": status,
                    "value": rgb_hex,
                }],
            })

    def send_ding_talk(self, content, unique_key):
        """
        发送钉钉报警
        :param content: 报警内容
        :param unique_key: 本次报警的唯一标识
        :return:
        """
        if not default_storage_redis.get(unique_key):
            default_storage_redis.set(unique_key, "1", WARNING_DELAY_TIME)
            title = "【颜色档案】异常报警"
            self.crawl_handler_page(DingTalk(LANDONG_ROBOT_TOKEN, title, content))

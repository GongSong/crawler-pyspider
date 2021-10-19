import json

from crawl_taobao_goods_migrate.config import CRAWL_SHOPS
from pyspider.helper.date import Date
from pyspider.helper.excel import Excel
from pyspider.libs.oss import oss
from pyspider.libs.sls import sls


class TmallOss:
    """
    天猫商品在oss的数据，输出Excel
    """

    def __init__(self, start_time: str, end_time: str):
        """

        :param start_time: eg. "2021-03-01"
        :param end_time: eg. "2021-04-01"
        """
        # 统计时间
        self.statistics_start_time = start_time
        self.statistics_end_time = end_time
        # 保存每个商品的统计数据
        self.save_sku = {}
        """
        按月份的统计保存数据, eg:      
        month_save_data = {
            "2021-03": {
                "monthly_sales_count": 25,  # 本期销量
                "whole_star": 25,  # 当月的总收藏(收藏数都是总数)
            },
            "2021-04": {
                "monthly_sales_count": 25,  # 本期销量
                "whole_star": 25,  # 当月的总收藏(收藏数都是总数)
            }
        }
        """
        self.month_save_data = {}
        self.oss_data_start_date = start_time
        self.oss_data_end_date = end_time

    def entry(self):
        for shop_id, shop_url in CRAWL_SHOPS.items():
            self.save_sku = {}
            self.month_save_data = {}
            print("开始导出店铺:{}的商品数据".format(shop_id))
            # 多线程跑数据

            excel_name = "{shop_id}-{date}".format(shop_id=shop_id, date=Date().now().format(full=False))
            begin_date = Date(self.oss_data_start_date)
            while True:
                path = "crawler/goods/tmall/{shop_id}/{start_date}".format(
                    shop_id=shop_id, start_date=begin_date.format(full=False).replace("-", "/") + "/")

                next_token = ''
                excel = self.get_excel()
                while True:
                    files, next_token = oss.list_objects(prefix=path, continuation_token=next_token, max_keys=1000)
                    print("files count:{}".format(len(files)))
                    for file in files:
                        try:
                            file_name = file.key
                            print(file_name)
                            file_obj = oss.get_object(file_name).resp.response.content
                            data = file_obj
                            json_data = json.loads(data)
                            self.value_to_excel(json_data)
                        except Exception as e:
                            print("err: {}".format(e.args))

                    if not next_token:
                        break
                if begin_date.format(full=False) == self.oss_data_end_date:
                    break
                begin_date.plus_days(1)
            # 导出数据
            for item_key, item_value in self.save_sku.items():
                excel.add_data(item_value)
            excel.export_file(file_name=excel_name)
            print("导出店铺:{}的商品数据完成".format(shop_id))

    def sls_entry(self):
        """
        获取 aliyun sls 的天猫商品数据
        :return:
        """
        from_time = Date.now().plus_months(-1).timestamp()
        to_time = Date.now().timestamp()
        sls.get_log_all("craw-robot", "tmall-goods", from_time, to_time)

    def value_to_excel(self, data):
        """
        把数据转为erp上传的对应字段
        :param data:
        :return:
        """
        # 商品ID
        goods_id = data.get('goods_id', '')
        # 保存sku的最新统计数据
        save_sku_goods = self.save_sku.get(goods_id, {})
        sku_update_time = data.get('update_time', '1970-01-01 08:00:01')
        # 商品划线价
        price = float(data.get('price', 0))
        # 统计时间最高价 - 默认给划线价
        period_highest_price = price
        # 统计时间最低价 - 默认给划线价
        period_lowest_price = price
        # 历史最低价 - 默认给划线价
        history_lowest_price_in = price
        # 上架时间
        added_time = save_sku_goods.get("added_time", "")

        if save_sku_goods:
            # 统计范围内
            if Date(self.statistics_start_time).to_day_start().timestamp() <= Date(sku_update_time).to_day_start() \
                    .timestamp() <= Date(self.statistics_end_time).to_day_start().timestamp():
                # 统计时间最高价
                if price > save_sku_goods.get("period_highest_price", 0):
                    period_highest_price = price
                # 统计时间最低价
                if price < save_sku_goods.get("period_lowest_price", 0):
                    period_lowest_price = price
                # 历史最低价
                if price < save_sku_goods.get("history_lowest_price_in", 0):
                    history_lowest_price_in = price
            else:
                if price < save_sku_goods.get("history_lowest_price_in", 0):
                    history_lowest_price_in = price
        else:
            added_time = data.get('update_time', '')

        # 本期销量
        monthly_sales_count = data.get('sales_count_monthly', 0)
        if isinstance(monthly_sales_count, str):
            if "100+" in monthly_sales_count:
                monthly_sales = 100 * period_highest_price
                monthly_sales_count = 100
            elif "200+" in monthly_sales_count:
                monthly_sales = 200 * period_highest_price
                monthly_sales_count = 200
            elif "400+" in monthly_sales_count:
                monthly_sales = 400 * period_highest_price
                monthly_sales_count = 400
            else:
                monthly_sales = int(monthly_sales_count) * period_highest_price
        else:
            monthly_sales = int(monthly_sales_count) * period_highest_price

        # 总收藏
        whole_star = data.get('star_number', 0)

        # 按月份的统计的数据
        month_date_str = Date(data.get('update_time', '')).format(full=False)[:-3]
        self.month_save_data[month_date_str] = {
            "monthly_sales_count": monthly_sales_count,  # 本期销量
            "whole_star": whole_star,  # 当月的总收藏(收藏数都是总数)
        }

        # 总销量
        total_sales_count = sum(
            [int(data_item.get("monthly_sales_count", 0)) for date_str, data_item in self.month_save_data.items()])

        # 本期收藏
        now_date_str = Date().now().format(full=False)[:-3]
        last_month_date_str = Date().now().plus_months(-1).format(full=False)[:-3]
        monthly_star = self.month_save_data.get(now_date_str, {}).get("whole_star", 0) - self.month_save_data.get(
            last_month_date_str, {}).get("whole_star", 0)

        color = ""
        for item_sku in data.get("sku", {}):
            if item_sku.get("stock", 0) > 0:
                color = item_sku.get("color", "")

        barcode = ""
        year_season = ""
        material = ""
        sales_channel_type = ""
        suitable_age = ""
        my_brand = ""
        goods_attr_list = data.get("goods_attr_list", [])
        for goods in goods_attr_list:
            item_str = goods
            if "货号" in item_str:
                barcode = item_str.split(':', 1)[1].strip()
            elif "年份季节" in item_str:
                year_season = item_str.split(':', 1)[1].strip()
            elif "材质成分" in item_str:
                material = item_str.split(':', 1)[1].strip()
            elif "销售渠道类型" in item_str:
                sales_channel_type = item_str.split(':', 1)[1].strip()
            elif "适用年龄" in item_str:
                suitable_age = item_str.split(':', 1)[1].strip()
            elif "品牌" in item_str:
                my_brand = item_str.split(':', 1)[1].strip()

        the_list = {
            'goods_id': goods_id,
            'title': data.get('goods_name', ''),
            'main_image': data.get('main_img', ''),
            'origin_price': data.get('original_price', 0),
            'price': price,
            'period_highest_price': period_highest_price,
            'period_lowest_price': period_lowest_price,
            'history_lowest_price_in': history_lowest_price_in,
            'category': data.get('category', ''),
            'goods_url': data.get('goods_url', ''),
            'added_time': added_time,
            'industry': data.get('industry', ''),
            'shop_name': data.get('shop_name', ''),
            'statistics_time': "{} - {}".format(self.statistics_start_time, self.statistics_end_time),
            'total_sales_count': total_sales_count,
            'monthly_sales_count': monthly_sales_count,
            'monthly_sales': monthly_sales,
            'monthly_star': monthly_star,
            'whole_star': whole_star,
            'whole_comments_count': data.get('comments_count', ''),
            'stock': data.get('stock', ''),
            'color': color,
            'barcode': barcode,
            'brand​': my_brand,
            'year_season': year_season,
            'material': material,
            'sales_channel_type': sales_channel_type,
            'suitable_age': suitable_age,
            'update_time': data.get('update_time', ''),
        }
        self.save_sku[goods_id] = the_list

    def get_excel(self):
        """
        定义表头及字段名
        :return:
        """
        return Excel() \
            .add_header('goods_id', '商品ID') \
            .add_header('title', '商品标题') \
            .add_header('main_image', '商品主图链接') \
            .add_header('origin_price', '商品价格') \
            .add_header('price', '商品划线价') \
            .add_header('period_highest_price', '统计时间最高价') \
            .add_header('period_lowest_price', '统计时间最低价') \
            .add_header('history_lowest_price_in', '历史最低价') \
            .add_header('category', '商品类目') \
            .add_header('goods_url', '商品链接') \
            .add_header('added_time', '上架时间') \
            .add_header('industry', '所属行业') \
            .add_header('shop_name', '所属店铺') \
            .add_header('statistics_time', '统计时间') \
            .add_header('total_sales_count', '总销量') \
            .add_header('monthly_sales_count', '本期销量') \
            .add_header('monthly_sales', '本期销售额(元)') \
            .add_header('monthly_star', '本期收藏') \
            .add_header('whole_star', '总收藏') \
            .add_header('whole_comments_count', '总评价') \
            .add_header('stock', '库存') \
            .add_header('color', '颜色') \
            .add_header('barcode', '货号') \
            .add_header('brand​', '品牌​') \
            .add_header('year_season', '年份季节') \
            .add_header('material', '材质成分') \
            .add_header('sales_channel_type', '销售渠道类型') \
            .add_header('suitable_age', '适用年龄') \
            .add_header('update_time', '数据更新时间')


if __name__ == '__main__':
    TmallOss("2021-04-01", "2021-04-01").entry()

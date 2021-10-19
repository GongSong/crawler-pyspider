import copy

from crawl_taobao_goods_migrate.model.task import Task
from pyspider.libs.base_crawl import *
from pyspider.helper.date import Date
from pyspider.helper.utils import get_tunnel_proxy
from crawl_taobao_goods_migrate.config import *
from cookie.model.data import Data as CookieData

import json


class GoodsDetails(BaseCrawl):
    """
    天猫商品详情抓取
    """

    URL = "https://detail.m.tmall.com/item.htm?id={}"

    def __init__(self, goods_id, use_proxy=True, set_cookies=True, priority=0):
        super(GoodsDetails, self).__init__()
        self.__set_cookies = set_cookies
        self.__priority = priority
        self.__goods_id = goods_id
        self.__use_proxy = use_proxy

    def crawl_builder(self):
        builder = CrawlBuilder() \
            .set_url(self.URL.format(self.__goods_id)) \
            .set_headers_kv('User-Agent', USER_AGENT) \
            .schedule_priority(self.__priority) \
            .schedule_age() \
            .set_timeout(GOODS_TIMEOUT) \
            .set_connect_timeout(GOODS_CONNECT_TIMEOUT) \
            .set_task_id(Task.get_task_id_goods_detail(self.__goods_id))

        if self.__set_cookies:
            cookies = CookieData.srand(CookieData.CONST_PLATFORM_TMALL_SHOP_GOODS)
            if not cookies:
                cookies = ""
            builder.set_cookies(cookies)

        if self.__use_proxy:
            builder.set_proxy(get_tunnel_proxy())

        return builder

    def parse_response(self, response, task):
        content = response.text
        # 商品链接
        goods_url = 'https://item.taobao.com/item.htm?id={}'.format(self.__goods_id)
        # 入库时间
        update_time = Date.now().format()

        # 商品不存在
        if "notfound" in response.url:
            return {
                "goods_id": self.__goods_id,
                "notfound": True,
                "response_url": response.url,
                "update_time": update_time,
            }

        processor_logger.info('开始解析淘宝商品: {}'.format(goods_url))
        if "_DATA_Detail" not in content or "_DATA_Mdskip" not in content:
            assert False, '未获取到商品: {} 的数据'.format(goods_url)

        data_detail = content.split('var _DATA_Detail =', 1)[1].split("</script>", 1)[0].strip()
        if data_detail.endswith(";"):
            data_detail = data_detail[:-1]
        js_data_detail = json.loads(data_detail)
        trade = js_data_detail.get('trade', {})
        seller = js_data_detail.get('seller', {})
        item = js_data_detail.get('item', {})
        props = js_data_detail.get('props', {})
        mock = js_data_detail.get('mock', {})
        rate = js_data_detail.get('rate', {})

        data_mdskip = content.split('var _DATA_Mdskip =', 1)[1].split("</script>", 1)[0].strip()
        processor_logger.info('data_mdskip: {}'.format(data_mdskip))
        js_data_mdskip = json.loads(data_mdskip)
        goods_item = js_data_mdskip.get('item', {})
        sku_core = js_data_mdskip.get('skuCore', {})
        sku_base = js_data_mdskip.get('skuBase', {})

        # 判断是否正确的拿到了商品内容
        # 商品是否存在
        # assert False, '未获取到商品: {} 的数据'.format(self.__goods_id)
        # 是否被删除
        be_deleted = False
        # 判断商品是否下架，True 为下架，False 为上架
        off_shelf = False if trade.get('buyEnable') else True
        if off_shelf:
            # 商品已下架，不保存商品数据
            return {
                "goods_id": self.__goods_id,
                "off_shelf": off_shelf,
                "response_url": response.url,
                "update_time": update_time,
            }

        # user ID: 店铺主体人的 ID
        user_id = seller.get('userId', 0)

        # 店铺ID
        shop_id = seller.get('shopId', 0)

        # 店铺名称
        shop_name = seller.get('shopName', "")

        # 店铺类型，B 为天猫 - 2，C 为淘宝 - 1
        shop_type = seller.get('shopType')
        shop_type = 1 if shop_type == 'C' else 2

        # 商品名称
        goods_name = item.get('title')

        # 商品主图
        main_img = 'https:' + item.get('images')[0]

        # 商品展示的轮播图
        polling_img = ['https:' + i for i in item.get('images')]

        # 被收藏数
        star_number = item.get('favcount')

        # 商品详情：产品参数 goods_attr_list
        goods_attr_list = props.get('groupProps')
        goods_attr_list = goods_attr_list[0].get('基本信息') if goods_attr_list else ''
        goods_attr_list = [':'.join(list(g.items())[0]) for g in goods_attr_list] if goods_attr_list else ''

        # 图文详情里的图片
        des_image = ''

        # 现价
        price = mock.get('price', {}).get('price', {}).get('priceText')

        # 原价
        original_price = mock.get('price', {}).get('extraPrices')
        original_price = original_price[0].get('priceText') if original_price else ''

        if not original_price and price:
            original_price = price

        # sku 数据
        sku = self.get_sku_info(sku_base, sku_core, original_price)

        # 获取促销信息
        promotion_date = mock.get('resource', {}).get('newBigPromotion')
        promotion_start_time = promotion_date if promotion_date else '1970-01-01'  # 促销开始时间
        promotion_end_time = promotion_date if promotion_date else '1970-01-01'  # 促销结束时间
        promotion_tag = mock.get('price', {}).get('priceTag')  # 促销价旁边的小字
        promotion_tag = promotion_tag[0].get('text', '') if promotion_tag else ''

        # 是否包邮
        postage_info = goods_item.get('delivery', {}).get('postage', '')
        if not postage_info:
            postage_price = 0
            postage = True
        elif '免运费' in postage_info or '快递: 0.00' in postage_info or '快递包邮' in postage_info:
            postage = False
            postage_price = 0
        elif '快递:' in postage_info:
            postage_price = float(postage_info.split('快递:', 1)[1].replace('元', '').strip())
            postage = True
        else:
            postage_price = 0
            postage = True

        # 预售信息，为空则无促销
        cainiao_ship = ''

        # 商品视频链接
        video_urls = goods_item.get('item', {}).get('videos')
        video_url = video_urls[0].get('url', '') if video_urls else ''

        # 月销量
        sales_count_monthly = goods_item.get("sellCount", 0)

        # 累计评价数
        comments_count = rate.get("totalCount", 0) if rate else 0

        # 库存
        stock = sum([i.get("stock", 0) for i in sku])

        # 商品类目
        category = self.category_list(goods_name)

        # 所属行业
        industry = self.industry_list(goods_name)

        # 保存数据
        # 入库
        processor_logger.info("商品：{}入库成功".format(goods_url))

        # 最终的数据
        data = {'goods_id': self.__goods_id, 'goods_url': goods_url, 'user_id': user_id, 'shop_id': shop_id,
                'shop_type': shop_type, 'sku': sku, 'des_image': des_image, 'star_number': star_number,
                'update_time': update_time, 'promotion_start_time': promotion_start_time, "category": category,
                'promotion_end_time': promotion_end_time, 'promotion_tag': promotion_tag, 'off_shelf': off_shelf,
                'be_deleted': be_deleted, 'postage': postage, 'postage_price': postage_price, 'goods_name': goods_name,
                'cainiao_ship': cainiao_ship, 'video_url': video_url, 'goods_attr_list': goods_attr_list,
                'original_price': original_price, 'price': price, 'shop_name': shop_name, 'main_img': main_img,
                'polling_img': polling_img, 'sales_count_monthly': sales_count_monthly, "stock": stock,
                "comments_count": comments_count, "industry": industry}

        # 保存数据 - oss
        date_str = Date.now().format(full=False)
        year, month, day = date_str.split("-")
        data_path = '{shop_id}/{year}/{month}/{day}/{goods_id}.json'.format(
            shop_id=shop_id, year=year, month=month, day=day, goods_id=self.__goods_id)
        file_path = oss.get_key(oss.CONST_TMALL_GOODS_PATH, data_path)
        oss_data = copy.deepcopy(data)
        binary_data = json.dumps(oss_data).encode("utf8")
        oss.upload_data(file_path, binary_data)

        data["data_path"] = data_path
        data["data_detail"] = data_detail[:200]
        return data

    def get_sku_info(self, sku_base, sku_core_api, original_price):
        """
        获取默认的商品假数据sku信息
        :param sku_base: 本商品的默认请求响应详情
        :param sku_core_api: API 缓存接口数据
        :param original_price: API 缓存接口数据
        :return:
        """
        sku_list = list()
        sku_name_dict = {
            '尺码': 'size',
            '颜色分类': 'color',
            '主要颜色': 'color',
            '颜色': 'color',
        }

        try:
            # 商品的 sku id 对应的价格和库存信息
            sku_core = sku_core_api.get('sku2info')

            # 商品的 sku 种类信息
            sku_props = sku_base.get('props')

            # 商品的 skus 和 种类信息 ID 的对应关系
            sku_relation = sku_base.get('skus')

            # 通过sku关系合并 sku_core 和 sku_props
            for sku in sku_relation:
                combine_dict = {}
                sku_id = str(sku.get('skuId'))
                prop_path = sku.get('propPath', "")

                # 合并价格和库存信息
                if sku_core.get(sku_id) is not None:
                    combine_dict.setdefault('price', sku_core.get(sku_id).get('price', {}).get('priceText'))
                    combine_dict.setdefault('stock', sku_core.get(sku_id).get('quantity', 0))
                    combine_dict.setdefault('sku_original_price', original_price)
                    combine_dict.setdefault('skuId', sku_id)

                # 合并尺码颜色等信息
                for prop in sku_props:
                    pid = str(prop.get('pid'))
                    name = prop.get('name')
                    values = prop.get('values')

                    if pid in prop_path:
                        prop_name = sku_name_dict.get(name, 'size')
                        for v in values:
                            vid = str(v.get('vid'))
                            v_name = v.get('name')
                            image = v.get('image', None)
                            if vid in prop_path:
                                combine_dict.setdefault(prop_name, v_name)
                                if image is not None:
                                    combine_dict.setdefault('image', 'https:' + image)

                sku_list.append(combine_dict)

        except Exception as e:
            processor_logger.exception(e)
            processor_logger.warning('解析商品的sku信息失败')
            sku_list = list()

        return sku_list

    def category_list(self, title):
        """
        类目表
        :param title:
        :return:
        """
        categories = {
            '针织衫/毛衣', '其他配件', '羽绒服', '夹克', '单鞋', '时装凉鞋', '围巾/丝巾/披肩', '休闲裤', '棉衣/棉服', '棉衣',
            'T恤', '商品类目', '卫衣/绒衫', '半身裙', '女装购物金', '西装', '毛呢大衣', '短外套', '乐福鞋（豆豆鞋）', '马夹',
            '毛针织衫', '休闲皮鞋', '背心吊带', '牛仔裤', '毛呢外套', '西服', '连衣裙', '休闲板鞋', '衬衫', '包头拖', '卫衣',
            '高帮鞋', '真丝上装', '皮衣', '毛衣', '时装靴', '蕾丝衫/雪纺衫', '风衣', '背心/马甲', '连体衣/裤', '穆勒鞋'
        }
        for item in categories:
            if item in title:
                return item
        return ""

    def industry_list(self, title):
        """

        :param title:
        :rtype: object
        """
        industries = ["男装", "女装/女士精品"]
        if "男" in title:
            return industries[0]
        elif "女" in title:
            return industries[1]
        else:
            return ""

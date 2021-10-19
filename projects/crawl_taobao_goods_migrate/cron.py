import random

import fire
import time

from bs4 import BeautifulSoup
from selenium.webdriver.support.wait import WebDriverWait

from cookie.model.data import Data as CookieData
from crawl_taobao_goods_migrate.config import MAX_ALL_INVENTORY, CRAWL_SHOPS, REPEAT_GOODS_LIMIT
from crawl_taobao_goods_migrate.model.result import Result
from crawl_taobao_goods_migrate.model.task import Task
from crawl_taobao_goods_migrate.page.export_tmall_goods import TmallOss
from crawl_taobao_goods_migrate.page.goods_details import GoodsDetails
from pyspider.helper.cookies_pool import CookiesPool
from pyspider.helper.date import Date
from pyspider.helper.utils import generator_list
from pyspider.libs.webdriver import Webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class Cron:
    def goods_polling(self, force=False):
        """
        轮询天猫商品详情
        :param force: 是否强制更新, False: 只更新当天未更新过的商品; True: 强制更新
        :return:
        """
        print('开始第三方商品的轮询')
        all_goods = self._get_filter_goods_ids(force)

        print('需要轮询的商品总数为: {}'.format(len(all_goods)))
        gen_list = generator_list(all_goods, 300)
        for _ge in gen_list:
            # 延迟入队的时间
            count = Task().find({'status': 1}).count()
            print('正在执行中的任务个数queue status:1 count: {}'.format(count))
            while count >= MAX_ALL_INVENTORY:
                time.sleep(int(count) / 5)
                count = Task().find({'status': 1}).count()
            for item_id in _ge:
                # 轮询所有的商品
                GoodsDetails(item_id, use_proxy=False).enqueue()
        print('轮询完成, 时间: {}，轮询数量为: {}'.format(Date.now().format(), len(all_goods)))

    def get_tmall_shop_goods(self, crawl_all, page):
        """
        获取天猫店铺下的所有商品ID索引

        :param crawl_all: 是否抓取全店的数据，默认是增量抓取
        :param page:
        :return:
        """
        driver = Webdriver().get_driver()
        cookies = CookieData.get(CookieData.CONST_PLATFORM_TAOBAO_SHOP, CookieData.CONST_COMMON_TMALL_SHOP)
        print("cookies", cookies)
        cookies_list = CookiesPool.cookies_to_dict(cookies)

        for shop_id, shop_url in CRAWL_SHOPS.items():
            print('shop_id', shop_id)
            print('shop_url', shop_url)
            driver.get(shop_url.format(1))
            for cookie in cookies_list:
                driver.add_cookie(cookie)
            print("添加cookies")
            time.sleep(3)
            try:
                self._crawl_pages(driver, shop_url, shop_id, crawl_all, page)
            except Exception as e:
                print("店铺:{}抓取失败".format(shop_id), e.args[0])

        driver.close()
        try:
            driver.quit()
        except:
            pass
        print("抓取完成,时间: {}".format(Date.now().format()))

    def tmall_goods_data_export(self, start_time: str, end_time: str):
        """
        导出天猫商品数据的表格
        :param start_time:
        :param end_time:
        :return:
        """
        TmallOss(start_time, end_time).entry()

    def _crawl_pages(self, driver, url, shop_id, crawl_all, page):
        """
        抓取店铺的商品
        :param driver:
        :param url:
        :param shop_id:
        :param crawl_all: 是否全量抓取
        :param page: 抓取的页码
        """
        page = int(page)
        delay_time = 15
        actual_url = url.format(page)
        print("抓取的页面地址:{}".format(actual_url))
        driver.get(actual_url)

        # 判断当前页是否正确展示，定位锚点
        WebDriverWait(driver, delay_time).until(EC.presence_of_element_located((By.CLASS_NAME, "J_TItems")))
        print("定位到了商品数据")
        had_next_page = self._extract_tmall_goods(driver.page_source, shop_id, crawl_all)

        # 随机暂停几秒，降低获取店铺商品的频率
        time.sleep(random.randint(3, 7))

        if had_next_page:
            self._crawl_pages(driver, url, shop_id, crawl_all, page + 1)

    def _extract_tmall_goods(self, page_source, shop_id, crawl_all) -> bool:
        """
        解析店铺页面的商品数据
        :param page_source:
        :param shop_id:
        :param crawl_all:
        :return: 是否有下一页, True: 有, False: 没有
        """
        print("解析店铺页面的商品数据")
        goods_ids = []
        repeat_goods_count = 0
        soup = BeautifulSoup(page_source, "lxml")
        items = soup.find("div", "J_TItems").find_all("dl", "item")
        now = Date().now().timestamp()

        if not crawl_all:
            # 根据是否全量抓取标签来确定是全量抓取还是增量抓取，增量抓取的话，只要重复商品数量达到比如10个，就停止抓取
            # 增量抓取商品，需要判断当前商品是否已存在，存在则跳过；
            # 一次性拿出所有的商品ID保存到内存，减少多次查库的压力
            goods_ids = self._get_all_goods_id(shop_id)

        for goods_item in items:
            goods_url = goods_item.find("dd", "detail").find("a")["href"]
            goods_id = goods_url.split("id=", 1)[1].split("&", 1)[0]
            goods_name = goods_item.find("dd", "detail").find("a").get_text().strip()
            print("goods_id", goods_id)
            print("goods_name", goods_name)

            if not crawl_all and goods_id in goods_ids:
                repeat_goods_count += 1
                if repeat_goods_count >= REPEAT_GOODS_LIMIT:
                    print("当前页重复商品超过:{}, 停止抓取本店铺:{}的商品".format(REPEAT_GOODS_LIMIT, shop_id))
                    return False

            doc = {
                "goods_id": goods_id,
                "goods_name": goods_name,
                "shop_id": shop_id,
                "update_time": now,
            }
            try:
                Result().insert_or_update_goods(doc)
            except Exception as e:
                print("商品ID写入mongodb error:", e.args[0])

        # 判断是否有下一页
        next_page_ele = soup.find("p", "ui-page-s").find("a", "ui-page-s-next")
        next_page_url = next_page_ele.get("href", "") if next_page_ele else ""
        print("next_page_url", next_page_url)
        if next_page_url:
            return True
        else:
            return False

    def _get_all_goods_id(self, shop_id):
        """
        获取所有的商品ID
        :param shop_id:
        :return:
        :return:
        """
        middle_set = set()
        all_goods = Result().find_all_goods(shop_id)
        for g in all_goods:
            goods_id = g.get('goods_id')
            middle_set.add(goods_id)
        return middle_set

    def _get_filter_goods_ids(self, force):
        """
        获取
        :param force: 是否强制更新
        :return:
        """
        shop_ids = [shop_id for shop_id, shop_url in CRAWL_SHOPS.items()]
        goods_set = set()
        goods_list = Result().find_all_shop_goods(shop_ids)
        for goods in goods_list:
            goods_set.add(goods.get('goods_id'))
        if not force:
            update_time = Date().now().to_day_start().timestamp()
            print("get update_time:{}".format(update_time))
            filter_goods_list = Result().find_filter_goods(shop_ids, update_time=update_time)
            for filter_goods in filter_goods_list:
                goods_id = filter_goods.get("result", {}).get('goods_id')
                if goods_id in goods_set:
                    goods_set.remove(goods_id)
        return goods_set


if __name__ == '__main__':
    fire.Fire(Cron)

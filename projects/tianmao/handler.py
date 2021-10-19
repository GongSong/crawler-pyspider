#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2018-12-11 15:44:45
# Project: tianmao
import time
import json
import random
import uuid
import datetime
import re
import requests

from pyquery import PyQuery as pq
from bs4 import BeautifulSoup

from pyspider.helper.date import Date
from pyspider.libs.base_handler import *
from pyspider.helper.cookies_pool import CookiesPool
from pyspider.helper.logging import processor_logger
from tianmao.config import *
from tianmao.model.tianmao import TianMao
from pyspider.message_queue.redis_queue import Queue


class Handler(BaseHandler):
    crawl_config = {
    }

    @every(minutes=1)
    def on_start(self):
        """
        天猫爬虫 入口
        :return:
        """
        # 商品评论 解析模块
        self.goods_comments_consumer()
        # 轮询队列生产模块
        self.polling()

    @config(age=1)
    def shop_tmall_parser(self, response):
        """
        天猫店铺详情解析
        :param response:
        :return:
        """
        processor_logger.info('开始天猫店铺解析部分')
        content = response.text
        shop_url = response.save.get('shop_url')

        soup = BeautifulSoup(content, 'lxml')
        shop_url = shop_url.split('tmall.com', 1)[0] + 'tmall.com'
        shop_name = soup.find('meta', attrs={'name': 'keywords'})['content']
        shop_type = 'shop_url'
        page = '1'

        processor_logger.info('把店铺URL: {} 加入队列'.format(shop_url))

        error_count = 0
        account_list = ['炫时科技:研发02']  # ['炫时科技', '炫时科技:研发02']
        cookies = CookiesPool.get_cookies_from_pool('sycm', random.choice(account_list))
        headers = {
            'User-Agent': USER_AGENT,
            'Cookie': cookies,
        }

        crawl_shop_url = '{}/i/asynSearch.htm?callback=jsonp126&mid=w-14571687321-0&wid=14571687321&path=' \
                         '/search.htm&search=y&scene=taobao_shop&orderType=newOn_desc&pageNo={}&tsearch=y'.format(
            shop_url, page)
        processor_logger.info("开始解析商家:{}".format(crawl_shop_url))

        self.crawl(
            crawl_shop_url,
            headers=headers,
            callback=self.shop_goods_parser,
            save={
                'page': page,
                'error_count': error_count,
                'headers': headers,
                'shop_url': shop_url,
            }
        )

        return {
            'save': response.save,
            'excelSize': len(response.content),
            'result': content,
            'shop_url': shop_url,
            'shop_name': shop_name,
            'shop_type': shop_type,
        }

    @config(age=1)
    def shop_goods_parser(self, response):
        """
        店铺商品 解析模块
        :param response:
        :return:
        """
        content = response.text
        page = int(response.save.get('page'))
        error_count = int(response.save.get('error_count'))
        shop_url = response.save.get('shop_url')
        headers = response.save.get('headers')

        # 每页的重复商品数量
        repeat_count = 0

        # 重试三次失败后退出
        if error_count > 3:
            return {
                'error_msg': 'retry times reach to 3, exit.',
                'save': response.save,
                'excelSize': len(response.content),
                'result': content,
                'page': page,
                'shop_url': shop_url,
            }

        data = content.replace('\\"', '')
        doc = pq(data)
        product = doc('dl.item')
        if product:
            for p in product:
                goods_url = 'https:' + pq(p)('a.J_TGoldData').attr('href')
                goods_id = goods_url.split('id=')[1].split('&')[0]
                if self.is_item_in_db(goods_id):
                    print("商品{}在数据库中，跳过添加。".format(goods_url))
                    repeat_count += 1
                else:
                    print("商品{}不在数据库中，继续添加。".format(goods_url))
                    goods_url = self.get_real_url(goods_url)
                    if not goods_url:
                        processor_logger.warning('不合法的goods url: {}'.format(goods_url))
                        return {
                            'error_msg': 'Invalid goods url: {}.'.format(goods_url),
                            'url': goods_url,
                        }

                    if 'tmall' in goods_url:
                        processor_logger.info("开始解析天猫的商品详情: {}".format(goods_url))
                        use_proxy = True
                        self.crawl(
                            goods_url,
                            headers=headers,
                            callback=self.parse_tmall_goods_details,
                            save={
                                'goods_url': goods_url,
                                'headers': headers,
                                'retry': RETRY_TIMES,
                                'use_proxy': use_proxy,
                            }
                        )
                    else:
                        processor_logger.warning("url：{}错误".format(goods_url))
            if repeat_count > 15:
                processor_logger.warning("本页: {} 重复商品数量为 {}，退出抓取.".format(page, repeat_count))
                return {
                    'exit_msg': 'repeat goods: {}, greater than 15, exit.'.format(repeat_count),
                    'save': response.save,
                    'excelSize': len(response.content),
                    'result': content,
                    'page': page,
                    'shop_url': shop_url,
                }
            processor_logger.info("第{}页的商品已入队列".format(page))
            crawl_shop_url = '{}/i/asynSearch.htm?callback=jsonp126&mid=w-14571687321-0&wid=14571687321&path=' \
                             '/search.htm&search=y&scene=taobao_shop&orderType=newOn_desc&pageNo={}&tsearch=y#{}' \
                .format(shop_url, page + 1, uuid.uuid4())
            time.sleep(1)
            self.crawl(
                crawl_shop_url,
                headers=headers,
                callback=self.shop_goods_parser,
                save={
                    'page': page + 1,
                    'error_count': error_count,
                    'headers': headers,
                    'shop_url': shop_url,
                }
            )
        else:
            # ---------------------------------反爬处理--------------------------------------------------
            processor_logger.warning("被反爬了，使用代理访问")
            account_list = ['炫时科技:研发02']  # ['炫时科技', '炫时科技:研发02']
            cookie_str = CookiesPool.get_cookies_from_pool('sycm', random.choice(account_list))
            error_count += 1
            headers = {
                'User-Agent': USER_AGENT,
                'Cookie': cookie_str,
            }
            crawl_shop_url = '{}/i/asynSearch.htm?callback=jsonp126&mid=w-14571687321-0&wid=14571687321&path=' \
                             '/search.htm&search=y&scene=taobao_shop&orderType=newOn_desc&pageNo={}&tsearch=y#{}' \
                .format(shop_url, page, uuid.uuid4())
            self.crawl(
                crawl_shop_url,
                headers=headers,
                callback=self.shop_goods_parser,
                save={
                    'page': page,
                    'error_count': error_count,
                    'headers': headers,
                    'shop_url': shop_url,
                }
            )

    @config(age=1)
    def parse_tmall_goods_details(self, response):
        """
        天猫商品sku解析
        :param response:
        :return:
        """
        content = response.text
        goods_url = response.save.get('goods_url')
        headers = response.save.get('headers')
        retry = int(response.save.get('retry'))
        use_proxy = response.save.get('use_proxy')
        callback_link = response.save.get('callback_link')

        # 解析商品id
        goods_id = goods_url.split('id=')[1].split('&')[0]

        # 判断是否是已被删除的商品，是则跳过抓取
        if self.is_deleted(goods_id):
            processor_logger.warning("商品: {}已被删除，跳过。".format(goods_id))
            return

        # 平台
        platform = 2

        # 解析商品页面
        try:
            soup = BeautifulSoup(content, 'lxml')

            # 判断商品是否下架
            off_shelf_soup = soup.find('strong', class_='sold-out-tit')
            if off_shelf_soup:
                off_shelf = True
                processor_logger.warning("商品: {}已下架".format(goods_id))
            else:
                off_shelf = False
            off_shelf_soup1 = soup.find('div', class_='error-notice-hd')
            off_shelf_soup2 = soup.find('div', class_='errorDetail')
            if off_shelf_soup1 or off_shelf_soup2:
                be_deleted = True
                processor_logger.warning("商品: {}已被删除".format(goods_id))
            else:
                be_deleted = False
            if be_deleted or off_shelf:
                user_id = ''
                shop_id = ''
                all_sku = ''
                goods_name = ''
                shop_name = ''
                main_img = ''
                des_image = ''
                polling_img = ''
                star_number = 0
                promotion_start_time = '1970-01-01'
                promotion_end_time = '1970-01-01'
                promotion_tag = ''
                postage = False
                postage_price = 0
                cainiao_ship = ''
                video_url = ''
                original_price = 0
                goods_attr_list = ''
                price = 0
                off_shelf = True
            else:
                meta_soup = soup.find('meta', attrs={"name": "microscope-data"})['content']

                # user ID
                user_id = meta_soup.split('userid=')[1].split(';')[0]

                # 店铺ID
                shop_id = meta_soup.split('shopId=')[1].split(';')[0]

                # 商品名称
                goods_name_soup = soup.find('meta', attrs={'name': 'keywords'})['content']
                goods_name = goods_name_soup.strip() if goods_name_soup else ''

                # 店铺名称
                shop_name_soup = soup.find('a', class_="slogo-shopname")
                shop_name = shop_name_soup.get_text().strip() if shop_name_soup else ''

                # 商品主图
                try:
                    main_img_soup = content.split('<img id="J_ImgBooth"', 1)[1].split('/>', 1)[0]
                    main_img = 'https:' + main_img_soup.split('src="', 1)[1].split('.jpg')[0] + '.jpg'
                except Exception as e:
                    processor_logger.warning('main_img 商品主图未获取到, error: {}'.format(e))
                    main_img = ''

                # 商品展示的轮播图
                try:
                    show_pages = content.split('<ul id="J_UlThumb"', 1)[1].split('</ul>', 1)[0]
                    img_list = []
                    show_pages_li = show_pages.split('<img src="')
                    for img in show_pages_li:
                        if 'img.alicdn.com' in img:
                            img_list.append('https:' + img.split('.jpg', 1)[0] + '.jpg')
                    polling_img = json.dumps(img_list, ensure_ascii=False)
                except Exception as e:
                    processor_logger.warning('没有轮播图 polling_img, error: {}'.format(e))
                    polling_img = ''

                # ---------获取sku接口的商品信息----------
                sku_map, jsitems = self.get_tmall_sku_info(content)
                if not sku_map:
                    processor_logger.warning("没有拿到商品: {} 的sku的mapping信息".format(goods_id))

                sku_url = 'https://mdskip.taobao.com/core/initItemDetail.htm?itemId={0}'.format(goods_id)

                if use_proxy:
                    # 使用cookies登陆
                    sku_api = self.get_tmall_requests_by_proxy(sku_url, goods_id)
                else:
                    # 直接请求商品链接获取的响应
                    headers = {
                        'User-Agent': USER_AGENT,
                        'Referer': 'https://detail.tmall.com/item.htm?spm=a220z.1000880.0.0.p0hlvy&id={}'.format(
                            goods_id),
                    }
                    sku_api = requests.get(sku_url, headers=headers, timeout=40).text
                    processor_logger.info("未使用代理的sku api: {}".format(sku_api))

                # 图文详情里的图片
                des_pic_url = 'http:' + jsitems['api']['httpsDescUrl']
                des_image = self.get_tmall_des_img(des_pic_url)

                # 被收藏数
                star_number = self.get_tmall_star_number(goods_id)

                # sku api
                sku_api = json.loads(sku_api)

                # 判断是否正确的拿到了数据
                if sku_api['defaultModel']:
                    processor_logger.info('拿到商品: {}的sku了'.format(goods_id))
                else:
                    processor_logger.info('没拿到商品: {}的sku'.format(goods_id))
                    raise TypeError

                # 是否包邮及邮费
                postage = sku_api['defaultModel']['deliveryDO']['deliverySkuMap']['default'][0][
                    'postageFree']
                try:
                    postage_price = sku_api['defaultModel']['deliveryDO']['deliverySkuMap']['default'][0]['postage'
                    ].split('快递:', 1)[1].strip()
                except Exception as e:
                    processor_logger.warning('包邮 error: {}'.format(e))
                    postage_price = 0
                postage_price = float(postage_price)

                # 预售信息，为空则无促销
                cainiao_ship = ''
                try:
                    cainiao_ship = sku_api['defaultModel']['deliveryDO']['cainiaoShipTime']
                    processor_logger.info('预售信息: {}'.format(cainiao_ship))
                except Exception as e:
                    processor_logger.info("无预售 {}".format(e))

                # 商品视频链接
                item = content.split('"imgVedioUrl":')
                if len(item) > 1:
                    video_url = 'https:' + item[1].split(',')[0][1:-1]
                    processor_logger.info('have video url: {}'.format(video_url))
                else:
                    processor_logger.info('no video')
                    video_url = ''

                # 店主ID
                seller_id = jsitems['rateConfig']['sellerId']

                # 添加评论队列
                comments_queue = Queue('tianmao:goods-comments', host='pyspider-redis')
                comments_queue.put('{};{}'.format(goods_id, seller_id))
                processor_logger.info('已写入评论队列')

                # 商品详情：产品参数 goods_attr_list
                goods_attr_list = self.get_tmall_goods_attr_list(content)  # ----------------没拿到--------------------

                # 获取促销信息
                # 原价
                promotion_start_time = '1970-01-01'  # 促销开始时间
                promotion_end_time = '1970-01-01'  # 促销结束时间
                promotion_tag = ''  # 促销价旁边的小字
                original_price = 0
                goods_details = sku_api['defaultModel']['itemPriceResultDO']['priceInfo']
                if goods_details:
                    for k, v in goods_details.items():
                        price = float(v['price'])
                        if original_price < price:
                            original_price = price
                        try:
                            promotion_end_time = Date(int(v['promotionList'][0]['endTime'] / 1000)).format()  # 促销结束时间
                            promotion_start_time = Date(
                                int(v['promotionList'][0]['startTime'] / 1000)).format()  # 促销开始时间
                            promotion_tag = v['promotionList'][0]['type']  # 促销价旁边的小字
                            break
                        except KeyError:
                            promotion_start_time = '1970-01-01'  # 促销开始时间
                            promotion_end_time = '1970-01-01'  # 促销结束时间
                            promotion_tag = ''  # 促销价旁边的小字
                            processor_logger.info('本店无促销活动')
                        break
                else:
                    promotion_start_time = '1970-01-01'  # 促销开始时间
                    promotion_end_time = '1970-01-01'  # 促销结束时间
                    promotion_tag = ''  # 促销价旁边的小字
                    processor_logger.info('本店无促销活动')

                # 合并拿到的sku数据
                all_sku = []
                sku_price = sku_api['defaultModel']['itemPriceResultDO']['priceInfo']

                # 现价
                try:
                    price = sku_price['def']['promotionList'][0]['price']
                except Exception as e:
                    processor_logger.warning('商品：{}没有price 现价（促销价）, 错误详情：{}'.format(goods_id, e.args[0]))
                    price = 0
                if not sku_map:
                    all_sku = [
                        {
                            "color": "",
                            "image": "",
                            "sku_original_price": "0",
                            "price": price,
                            "stock": 0,
                            "skuId": "",
                            "size": ""
                        }
                    ]
                for item in sku_map:
                    each_sku = {}
                    if item in sku_price:
                        try:
                            each_sku['color'] = sku_map[item]['name']
                            each_sku['image'] = sku_map[item]['img']
                        except Exception as e:
                            processor_logger.warning('商品：{}没有color或者image, 错误详情：{}'.format(goods_id, e.args[0]))
                            each_sku['color'] = ''
                            each_sku['image'] = ''
                        each_sku['sku_original_price'] = sku_map[item]['price']
                        try:
                            each_sku['price'] = sku_price[item]['promotionList'][0]['price']
                            if price < float(each_sku['price']):
                                price = float(each_sku['price'])
                        except Exception as e:
                            processor_logger.warning('商品：{}没有price现价, 错误详情：{}'.format(goods_id, e.args[0]))
                            each_sku['price'] = ''
                        each_sku['stock'] = sku_map[item]['stock']
                        each_sku['skuId'] = item
                        try:
                            each_sku['size'] = sku_map[item]['size']
                        except Exception as e:
                            processor_logger.info('商品：{}没有size, 错误详情：{}'.format(goods_id, e.args[0]))
                            each_sku['size'] = ''
                    if each_sku:
                        all_sku.append(each_sku)
                all_sku = json.dumps(all_sku, ensure_ascii=False) if all_sku else ''

        except Exception as e:
            processor_logger.warning("重试次数还剩:{}次".format(retry))
            if retry < 1:
                processor_logger.error('重试次数达到{}次，退出爬虫'.format(RETRY_TIMES))
                return {
                    'error_msg': '重试次数达到{}次，退出爬虫'.format(RETRY_TIMES),
                    'save': response.save,
                    'excelSize': len(response.content),
                    'result': content,
                    'goods_url': goods_url,
                    'headers': headers,
                }
            processor_logger.warning("商品页面详情出错：{}".format(e.args))
            processor_logger.warning('请求失败,被反爬了，暂停20s再次请求')
            self.crawl(
                goods_url,
                headers=headers,
                callback=self.parse_tmall_goods_details,
                save={
                    'goods_url': goods_url,
                    'headers': headers,
                    'callback_link': callback_link,
                    'use_proxy': True,
                    'retry': retry - 1,
                }
            )
            return

        # 入库时间
        update_time = Date.now().format()

        if TianMao().find({
            'result.goods_id': goods_id,
            'result.be_deleted': {'$exists': 'true'},
        }).count() < 1:
            # 入库
            processor_logger.info("商品：{}入库成功".format(goods_id))
            return {
                'save': response.save,
                'goods_id': goods_id,
                'goods_url': goods_url,
                'user_id': user_id,
                'shop_id': shop_id,
                'shop_type': platform,
                'sku': all_sku,
                'des_image': des_image,
                'star_number': star_number,
                'update_time': update_time,
                'promotion_start_time': promotion_start_time,
                'promotion_end_time': promotion_end_time,
                'promotion_tag': promotion_tag,
                'off_shelf': off_shelf,
                'be_deleted': be_deleted,
                'postage': postage,
                'postage_price': postage_price,
                'goods_name': goods_name,
                'cainiao_ship': cainiao_ship,
                'video_url': video_url,
                'goods_attr_list': goods_attr_list,
                'original_price': original_price,
                'price': price,
                'shop_name': shop_name,
                'main_img': main_img,
                'polling_img': polling_img,
            }
        else:
            # 更新
            if off_shelf and shop_id == '':
                # 已经下架了，第一次抓取就已经是下架状态
                data = {
                    'update_time': update_time,
                    'off_shelf': off_shelf,
                }
                TianMao().update(
                    {
                        'result.goods_id': goods_id,
                        'result.be_deleted': {'$exists': 'true'},
                    },
                    {"$set": data},
                )
            elif be_deleted:
                # 已经被删除了
                data = {
                    'update_time': update_time,
                    'be_deleted': be_deleted,
                    'off_shelf': True,
                }
                TianMao().update(
                    {
                        'result.goods_id': goods_id,
                        'result.be_deleted': {'$exists': 'true'},
                    },
                    {"$set": data},
                )
            else:
                data = {
                    'goods_url': goods_url,
                    'user_id': user_id,
                    'shop_id': shop_id,
                    'shop_type': platform,
                    'sku': all_sku,
                    'des_image': des_image,
                    'star_number': star_number,
                    'update_time': update_time,
                    'promotion_start_time': promotion_start_time,
                    'promotion_end_time': promotion_end_time,
                    'promotion_tag': promotion_tag,
                    'off_shelf': off_shelf,
                    'be_deleted': be_deleted,
                    'postage': postage,
                    'postage_price': postage_price,
                    'goods_name': goods_name,
                    'cainiao_ship': cainiao_ship,
                    'video_url': video_url,
                    'goods_attr_list': goods_attr_list,
                    'original_price': original_price,
                    'price': price,
                    'shop_name': shop_name,
                    'main_img': main_img,
                    'polling_img': polling_img,
                }
                TianMao().update(
                    {
                        'result.goods_id': goods_id,
                        'result.be_deleted': {'$exists': 'true'},
                    },
                    {"$set": data},
                )
                processor_logger.info("商品{}存在数据库中，已更新".format(goods_id))
        if callback_link:
            try:
                requests.get(callback_link, headers=self.headers, timeout=20)
                processor_logger.info("已请求回调链接：{}".format(callback_link))
            except Exception as e:
                processor_logger.exception('callback_link error : {}'.format(e))
            processor_logger.info("商品{}存在数据库中，已更新".format(goods_id))

    @every(seconds=10)
    def goods_comments_consumer(self):
        """
        天猫商品评论 详情消费队列
        每10s开始一次队列消费
        :return:
        """
        try:
            headers = {
                'User-Agent': USER_AGENT,
            }
            comments_queue = Queue('tianmao:goods-comments', host='pyspider-redis')
            item = comments_queue.get_nowait()
            goods_id = item.split(';')[0]
            seller_id = item.split(';')[1]
            page = 1
            comments_url = 'https://rate.tmall.com/list_detail_rate.htm?itemId={0}&sellerId={1}&currentPage={2}' \
                .format(goods_id, seller_id, page)
            self.crawl(
                comments_url,
                headers=headers,
                callback=self.parse_tmall_goods_comments,
                save={
                    'comments_url': comments_url,
                    'headers': headers,
                    'goods_id': goods_id,
                    'seller_id': seller_id,
                    'page': page,
                }
            )

        except Exception as e:
            processor_logger.error('天猫商品评论 详情消费队列 error: {}'.format(e))
            processor_logger.error('队列中没有 goods-comments 商品评论')

    @config(age=1)
    def parse_tmall_goods_comments(self, response):
        """
        天猫商品 评论 解析
        :param response:
        :return:
        """
        content = response.text
        headers = response.save.get('headers')
        goods_id = response.save.get('goods_id')
        seller_id = int(response.save.get('seller_id'))
        page = int(response.save.get('page'))

        try:
            comments_req = content.text[15:]
            result = json.loads(comments_req)
            comments = result['rateList']
            for c in comments:
                # 评论入库时间
                create_time = Date.now().format()
                comments_id = c['id'],  # 评论ID
                comments_content = c['rateContent'],  # 评论内容
                comments_pic_color = c['auctionSku'],  # 颜色分类
                comments_site = c['cmsSource'],  # 网址类别
                comments_name = c['displayUserNick'],  # 评论者
                comments_time = c['rateDate'],  # 评论时间
                comments_pic = ['https:' + _ for _ in c['pics']],  # 评论图片
                comments_son_url = 'https://www.baidu.com/#{}'.format(uuid.uuid4())
                self.crawl(
                    comments_son_url,
                    headers=headers,
                    callback=self.parse_tmall_goods_comments_son,
                    save={
                        'content': c,
                        'goods_id': goods_id,
                        'create_time': create_time,
                        'comments_id': comments_id,
                        'comments_content': comments_content,
                        'comments_pic_color': comments_pic_color,
                        'comments_site': comments_site,
                        'comments_name': comments_name,
                        'comments_time': comments_time,
                        'comments_pic': comments_pic,
                    }
                )

            # 下一页
            # last_page 代表评论总页数
            last_page = int(result['paginator']['lastPage'])
            # comments 是具体评论
            if page < last_page:
                next_page = 'https://rate.tmall.com/list_detail_rate.htm?itemId={0}&sellerId={1}&currentPage={2}' \
                    .format(goods_id, seller_id, page + 1)
                self.crawl(
                    next_page,
                    headers=headers,
                    callback=self.parse_tmall_goods_comments,
                    save={
                        'comments_url': next_page,
                        'headers': headers,
                        'goods_id': goods_id,
                        'seller_id': seller_id,
                        'page': page + 1,
                    }
                )
            else:
                processor_logger.warning('评论的最后一页了, 退出')
        except Exception as e:
            processor_logger.error('天猫商品 评论 解析 error: {}'.format(e))
            processor_logger.error('获取本页：{} 评价详情失败，开始获取下一个商品。'.format(page))
            return {
                'error_msg': 'parse commens error: {}, exit.'.format(e),
                'save': response.save,
                'excelSize': len(response.content),
                'result': content,
            }

    @config(age=1)
    def parse_tmall_goods_comments_son(self, response):
        """
        天猫商品 评论内容 入库
        :param response:
        :return:
        """
        content = response.save.get('content')
        goods_id = response.save.get('goods_id')
        create_time = response.save.get('create_time')
        comments_id = response.save.get('comments_id')
        comments_content = response.save.get('comments_content')
        comments_pic_color = response.save.get('comments_pic_color')
        comments_site = response.save.get('comments_site')
        comments_name = response.save.get('comments_name')
        comments_time = response.save.get('comments_time')
        comments_pic = response.save.get('comments_pic')
        return {
            'content': content,
            'goods_id': goods_id,
            'create_time': create_time,
            'comments_id': comments_id,
            'comments_content': comments_content,
            'comments_pic_color': comments_pic_color,
            'comments_site': comments_site,
            'comments_name': comments_name,
            'comments_time': comments_time,
            'comments_pic': comments_pic,
        }

    @every(minutes=24 * 6)
    def polling(self):
        """
        轮询脚本，24小时执行一次
        """
        account_list = ['炫时科技:研发02']  # ['炫时科技', '炫时科技:研发02']
        cookies = CookiesPool.get_cookies_from_pool('sycm', random.choice(account_list))
        headers = {
            'User-Agent': USER_AGENT,
            'Cookie': cookies,
        }

        goods = TianMao().find({
            'result.goods_id': {'$exists': 'true'},
            'result.be_deleted': {'$exists': 'true'},
        })
        shops = TianMao().find({
            'result.shop_type': {'$exists': 'true'},
            'result.shop_url': {'$exists': 'true'},
        })
        if goods.count() < 1:
            processor_logger.warning("数据库没有商品")
        else:
            processor_logger.info("需要轮询的商品个数:{}".format(goods.count()))
            for g in goods:
                goods_url = g.get('result').get('goods_url')
                goods_url = self.get_real_url(goods_url)
                if not goods_url:
                    processor_logger.warning('不合法的goods url: {}'.format(goods_url))
                    return {
                        'error_msg': 'Invalid goods url: {}.'.format(goods_url),
                        'url': goods_url,
                    }

                if 'tmall' in goods_url:
                    processor_logger.info("开始解析天猫的商品详情: {}".format(goods_url))
                    use_proxy = True
                    self.crawl(
                        goods_url,
                        headers=headers,
                        callback=self.parse_tmall_goods_details,
                        save={
                            'goods_url': goods_url,
                            'headers': headers,
                            'retry': RETRY_TIMES,
                            'use_proxy': use_proxy,
                        }
                    )
                #     goodsTmallDetailsParser.parse_goods(goods_url, callback_link)
                else:
                    processor_logger.warning("url：{}错误".format(goods_url))
                processor_logger.info("已push商品：{}".format(goods_url))
        if shops.count() < 1:
            processor_logger.info("数据库没有 店铺")
        else:
            print("需要轮询的 店铺 个数:{}".format(shops.count()))
            for s in shops:
                shop_url = s.get('result').get('shop_url')
                print("开始解析店铺：{}".format(shop_url))
                if 'tmall' in shop_url:
                    print("天猫商铺，开始解析")
                    self.crawl(
                        shop_url,
                        headers=headers,
                        callback=self.shop_tmall_parser,
                        save={
                            'shop_url': shop_url,
                        }
                    )
                elif 'taobao' in shop_url:
                    print("Taobao 商铺，开始解析")
                    pass
                else:
                    processor_logger.warning('错误的店铺url!!')

    def is_item_in_db(self, goods_id):
        '''
        判断 goods id 是否在数据库中
        :param goods_id: 商品ID
        '''
        if TianMao().find({'result.goods_id': goods_id}).count() < 1:
            # 数据库没有该goods ID
            return False
        else:
            # 数据库有该goods ID
            return True

    def get_real_url(self, goods_url):
        """
        获取商品链接的真实URL
        :param goods_url:
        :return:
        """
        headers = {
            'User-Agent': USER_AGENT,
        }
        real_url = ''

        # 解析商品id
        try:
            goods_id = goods_url.split('id=')[1].split('&')[0]
        except Exception as e:
            processor_logger.error("商品链接获取goods id失败：{}".format(e))
            processor_logger.error("商品:{}入库失败，请检查goods url是否合法".format(goods_url))
            return ''

        req = requests.get(goods_url, headers=headers).text
        if 'taobao' in goods_url:
            if 'shopUrl' in req:
                try:
                    url = req.split('shopUrl', 1)[1].split(',', 1)[0]
                    if 'tmall' in url:
                        real_url = 'https://detail.tmall.com/item.htm?id={}'.format(goods_id)
                except Exception as e:
                    processor_logger.error('获取天猫真实url error: {}'.format(e))
            else:
                real_url = goods_url
        elif 'tmall' in goods_url:
            real_url = goods_url
        else:
            real_url = ''
        return real_url

    def is_deleted(self, goods_id):
        """
        判断商品是否已经被删除
        :param goods_id:
        :return:
        """
        goods = TianMao().find_one({
            'result.goods_id': goods_id,
            'result.be_deleted': {'$exists': 'true'},
        })
        if goods is not None and goods.be_deleted:
            processor_logger.warning('此商品: {} 已被删除'.format(goods_id))
            return True
        else:
            return False

    def get_tmall_requests_by_proxy(self, sku_url, goods_id):
        '''
        使用代理获取天猫响应详情
        :param sku_url: 商品链接
        :return: sku api
        '''

        # cookie_str = utils.get_cookies_from_pool('temp_alibaba', 'icy旗舰店_天猫')
        account_list = ['炫时科技:研发02']  # ['icy旗舰店:开发', 'icy旗舰店:研发']
        cookie_str = CookiesPool.get_cookies_from_pool('sycm', random.choice(account_list))
        headers = {
            'User-Agent': USER_AGENT,
            'Referer': 'https://detail.tmall.com/item.htm?spm=a220z.1000880.0.0.p0hlvy&id={}'.format(goods_id),
            'Cookie': cookie_str,
        }
        try:
            sku_api = requests.get(sku_url, headers=headers, timeout=30).text
            processor_logger.info("未获取到代理IP 的 sku api: {}".format(sku_api))
            test_sku_api = json.loads(sku_api.strip())
            if test_sku_api['isSuccess']:
                processor_logger.info('拿到商品的sku了')
        except Exception as e:
            processor_logger.error("sku api error: {}".format(e))
            processor_logger.info('没拿到商品的sku')
            sku_api = ''
        return sku_api

    def get_tmall_des_img(self, img_url):
        '''
        获取商品的描述图片
        '''
        headers = {
            'User-Agent': USER_AGENT,
            'Referer': TMALL_REFERER,
        }
        des_image = []
        try:
            des_req = requests.get(img_url, headers=headers, timeout=30).text
            tem_l = BeautifulSoup(des_req, 'lxml').find_all('img')
            for l in tem_l:
                des_image.append(l['src'])
            des_image = json.dumps(des_image, ensure_ascii=False) if des_image else ''
        except Exception as e:
            processor_logger.exception("get_des_img 错误详情: {}".format(e))
        return des_image

    def get_tmall_star_number(self, goods_id):
        '''
        获取店铺的收藏数
        '''
        headers = {
            'User-Agent': USER_AGENT,
            'Referer': TMALL_REFERER,
        }
        dy_url = 'https://count.taobao.com/counter3?callback=jsonp242&keys=SM_368_dsr-581746910,ICCP_1_' + goods_id
        try:
            dy_req = requests.get(dy_url, headers=headers, timeout=30).text
            dy_req = dy_req[9:-2]
            star_number = int(dy_req.split(":")[1].split(",")[0])
        except Exception as e:
            processor_logger.error("解析店铺的收藏数出错：{}".format(e))
            star_number = 0
        return star_number

    def get_tmall_goods_attr_list(self, content):
        '''
        获取 商品详情：产品参数
        :return: str
        '''
        goods_attr_list = []
        try:
            attr_list = content.split('<ul id="J_AttrUL">', 1)[1].split('</ul>', 1)[0]
            attr_list_li = attr_list.split('</li>')
            for attr in attr_list_li:
                if 'title' in attr:
                    replaced_item = attr.split('>', 1)[1].strip().replace('&nbsp;', '')
                    goods_attr_list.append(replaced_item)
        except Exception as e:
            processor_logger.exception("错误详情：{}".format(e))
        goods_attr_list = json.dumps(goods_attr_list, ensure_ascii=False) if goods_attr_list else ''
        return goods_attr_list

    def get_tmall_sku_info(self, content):
        '''
        获取默认的商品假数据sku信息
        :param content: 本商品的默认请求响应详情
        :return: 假数据sku信息
        '''
        # 正则出api的内容
        pattern = re.compile('TShop.Setup\((.*?)</script>', re.S)
        api = re.findall(pattern, content)
        api = api[0].strip()
        api = api[:-7].strip()
        api = api[:-2].strip()

        # json items
        jsitems = json.loads(api)

        # 获取商品的尺码，颜色，库存，价格信息
        processor_logger.info("开始获取商品的尺码颜色库存价格信息。")
        try:
            g_details = jsitems['valItemInfo']
        except Exception as e:
            processor_logger.warning('商品的尺码颜色获取错误: {}'.format(e))
            g_details = ''

        # 尺码下面不同颜色的商品图
        diff_color_goods_pic = {}
        try:
            property_pics = jsitems['propertyPics']
        except Exception as e:
            processor_logger.error("错误信息：{}".format(e))
            processor_logger.error("没有商品尺码下的图片信息。")
            property_pics = ''

        if property_pics:
            for k, v in property_pics.items():
                if k != 'default':
                    # 尺码下面不同颜色的商品图
                    diff_color_goods_pic[k[1:-1]] = 'https:' + v[0]
        else:
            # 没有尺码下的商品图
            processor_logger.info("没有尺码下的商品图.")
        if g_details:  # and diff_color_goods_pic:
            sku_map = self.get_goods_sku(g_details, diff_color_goods_pic)
            processor_logger.info('成功获取 sku map')
        else:
            processor_logger.info('获取 sku map 失败')
            sku_map = ''

        return sku_map, jsitems

    def get_goods_sku(self, info, diff_color_goods_pic):
        '''
        返回商品的尺码，颜色，库存，价格 dict
        :param info: 商品的颜色，尺码，颜色，库存等信息
        :param diff_color_goods_pic: 商品的不同颜色对应的颜色图
        :return:
        '''
        return_dic = {}
        sku_map = info['skuMap']
        for k, v in sku_map.items():
            for key in k.split(';'):
                # 获取tem_k的值
                if '1627207' in key:
                    tem_k = key
                    break
            if diff_color_goods_pic:
                if tem_k in diff_color_goods_pic:
                    return_dic.setdefault(v['skuId'], {'stock': v['stock'], 'price': v['price'], "name": '',
                                                       "img": diff_color_goods_pic[tem_k], "size": ''})
                else:
                    return_dic.setdefault(v['skuId'], {'stock': v['stock'], 'price': v['price'], "name": '',
                                                       "img": '', "size": ''})
            else:
                return_dic.setdefault(v['skuId'], {'stock': v['stock'], 'price': v['price'], "name": '',
                                                   "img": '', "size": ''})

        sku_list = info['skuList']
        for s in sku_list:
            sku_name = s['names'].split(' ')
            l_name = sku_name[1] if len(sku_name) > 2 else sku_name[0]
            l_size = sku_name[0] if len(sku_name) > 2 else ''
            return_dic[s['skuId']]['name'] = l_name
            return_dic[s['skuId']]['size'] = l_size
        return return_dic

    def parse_tmall_shop(self, url):
        """
        天猫店铺 API 接口 注册入口
        :param url:
        :return:
        """
        account_list = ['炫时科技:研发02']  # ['炫时科技', '炫时科技:研发02']
        cookies = CookiesPool.get_cookies_from_pool('sycm', random.choice(account_list))
        headers = {
            'User-Agent': USER_AGENT,
            'Cookie': cookies,
        }
        self.crawl(
            url,
            headers=headers,
            callback=self.shop_tmall_parser,
            save={
                'shop_url': url,
            }
        )

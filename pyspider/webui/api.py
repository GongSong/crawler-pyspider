#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-10-19 16:23:55

from __future__ import unicode_literals

from flask import render_template, request, json
from flask import Response

from monitor_icy_comments_migrate.model.barcode_es import BarcodeES
from monitor_icy_comments_migrate.model.result import Result

from .app import app

from monitor_shop_goods.model.shop import Shop
from backstage_data_migrate.model.backstage_migrate import Backstage
from weipinhui_migrate.model.weipinhui import Weipinhui

from tianmao.handler import Handler as tm_handler
from tianmao.model.tianmao import TianMao

from crawl_taobao_goods_migrate.model.result import Result as TaobaoGoodsResult
from crawl_taobao_goods_migrate.page.goods_details import GoodsDetails
from crawl_taobao_goods_migrate.page.shop_details import ShopDetails

from pyspider.helper.date import Date
from pyspider.message_queue.redis_queue import Queue


@app.route('/apis/monitor_shop_goods', methods=['GET', 'POST'])
def mshop_goods():
    """
    监控商品上下架的API接口
    :return:
    """
    goods_id = str(request.args.get('goods_id', ''))
    goods_type = int(request.args.get('goods_type', 0))

    if request.method == 'POST':
        if goods_type == 0:
            msg = {
                'msg': 'there is no goods_type, please try again.',
                'data': '',
            }
            msg = json.dumps(msg)
            return msg, 404
        goods = Shop().find({'goods_id': goods_id})
        count = goods.count()
        if count == 0:
            now = Date.now().format()
            data = {
                'goods_id': goods_id,
                'goods_type': goods_type,
                'status': False,
                'update_time': now,
            }
            Shop().insert(data)
            msg = {
                'msg': 'Successful registered goods: {}.'.format(goods_id),
                'data': '',
            }
            msg = json.dumps(msg)
            return msg, 200
        else:
            msg = {
                'msg': 'Existing goods: {}'.format(goods_id),
                'data': '',
            }
            msg = json.dumps(msg)
            return msg, 400
    return '未写get逻辑', 200


@app.route('/apis/monitor_icy_comments/comments')
def monitor_icy_comments():
    """
    icy评论的获取接口
    :return:
    """
    return_dict = {}
    # 货号
    g_id = str(request.args.get('id', ''))
    # 商品类别，淘宝1，天猫2，京东3
    shop_type = int(request.args.get('shopType', 0))
    # 页码数
    page = int(request.args.get('page', 1))
    # 分页每页大小
    page_size = int(request.args.get('pageSize', 20))
    page = page - 1 if page > 0 else 0
    comments = Result().find_comment_by_barcode(shop_type, g_id, page, page_size)
    if not comments:
        return_dict['result'] = 1
        return_dict['msg'] = '未获取到对应的icy评论信息'
        return_dict['data'] = {}
    else:
        return_dict['result'] = 0
        return_dict['msg'] = '正常返回评论数据。'
        return_dict['data'] = {'list': comments}
    return json.dumps(return_dict), 200


@app.route('/apis/monitor_icy_comments/comments/relationship')
def monitor_icy_comments_id():
    """
    icy商品的货号和商品ID的对应关系
    :return:
    """
    return_dict = {}
    # 货号
    g_id = str(request.args.get('id', ''))
    # 页码数
    page = int(request.args.get('page', 1))
    # 分页每页大小
    page_size = int(request.args.get('pageSize', 20))
    page = page - 1 if page > 0 else 0
    goods_list = BarcodeES().get_barcode_goods_id_relationship(g_id, page, page_size)
    if not goods_list:
        return_dict['result'] = 1
        return_dict['msg'] = '未获取到货号ID的对应关系'
        return_dict['data'] = {}
        return json.dumps(return_dict), 200
    else:
        return_dict['result'] = 0
        return_dict['msg'] = '已获取到货号ID的对应关系'

        return_dict['data'] = goods_list
        return json.dumps(return_dict), 200


@app.route('/apis/backstage_data/data')
def backstage_data():
    """
    后台数据项目的数据获取接口
    :return:
    """
    return_result = {}
    # 要获取数据的渠道(网站) eg：taobao, jingdong, tmall
    channel = str(request.args.get('channel', ''))
    # 时间戳: 天, eg:2018-02-13
    timestamp = request.args.get('timestamp', '')
    # 数据类型, eg:访客数
    data_type = request.args.get('data_type', '')
    # 按照小时返回数据
    hour = request.args.get('hour', '')

    transform = {
        'taobao': {
            'website': 'sycm:taobao',
        },
        'tmall': {
            'website': 'sycm:tmall',
        },
        'tmall_outlets': {
            'website': 'sycm:tmall_outlets',
        },
        'jingdong': {
            'website': 'jingdong',
        },
        'redbook': {
            'website': 'redbook',
        },
        'redbook:flow': {
            'website': 'redbook',
        },
    }
    website_dict = transform.get(channel, '')

    if website_dict != '':
        website = website_dict['website']
        builder = {
            'result.website': website,
            'result.data_type': data_type,
            'result.create_time': timestamp,
        }
        if hour:
            hour = Date(hour).to_hour_start().timestamp()
            create_time = Date(hour).to_hour_start().format()
            builder['result.hour'] = hour
            builder['result.create_time'] = create_time
        my_data = Backstage().find(builder)
        if my_data.count() < 1:
            return_result['result'] = 1
            return_result['msg'] = "没有获取到 {} 的数据: {}".format(channel, data_type)
            return_result['data'] = ''
            return json.dumps(return_result)
        else:
            return_data = []
            for d in my_data:
                js_data = json.loads(d['result']['data']) if d['result']['data'] else ''
                return_data.append(js_data)
            return_result['result'] = 0
            return_result['msg'] = "获取到了 {} 的数据: {}".format(channel, data_type)
            return_result['data'] = return_data
            return json.dumps(return_result)
    else:
        return_result['result'] = 1
        return_result['msg'] = "未输入 channel，请重新输入"
        return_result['data'] = ''
        return json.dumps(return_result)


@app.route('/apis/crawl_taobao_shop/shop-suspend')
def crawl_taobao_goods_banner_img():
    """
    第三方商品店铺的banner图获取接口
    暂停这个接口
    :return:
    """
    # 店铺URL
    shop_url = request.args.get('shop_url', '')
    # 回调链接
    callback_link = request.args.get('callback_link', '')
    # 强制更新
    force = request.args.get('force', '')

    # 初始化数据
    return_dic = {}

    if not shop_url:
        return_dic['result'] = 1
        return_dic['msg'] = "店铺URL没有输入，请重新输入"
        return_dic['data'] = ''
        return json.dumps(return_dic), 200

    shop_id = shop_url.split('//shop', 1)[1].split('.taobao.com', 1)[0]

    result = {}
    if not force:
        result = TaobaoGoodsResult().find_shop_by_id(shop_id)

    if result:
        return_dic['result'] = 0
        return_dic['msg'] = '已获取商品:{}的详情'.format(shop_url)
        shop = result.get('result')
        pop_words = ['result', 'excelSize']
        for word in pop_words:
            if word in shop:
                shop.pop(word)
        return_dic['data'] = shop
    # 如果没有店铺可以返回，就入库爬取
    else:
        priority = 0
        if force:
            priority = 2
        elif callback_link:
            priority = 1
        ShopDetails(shop_url, callback_link=callback_link, priority=priority).enqueue()
        return_dic['result'] = 0
        return_dic['msg'] = "开始抓取: {}, 优先级：{}".format(shop_url, priority)
        return_dic['callback_link'] = "callback_link: ({})".format(callback_link)

    return json.dumps(return_dic), 200


@app.route('/apis/crawl_taobao_shop/goods-details', methods=['GET', 'POST'])
def crawl_taobao_goods_goods_details():
    """
    第三方商品的商品详情获取接口
    :return:
    """
    # 商品URL
    goods_url = request.args.get('goods_url', '')
    # 回调链接
    callback_link = request.args.get('callback_link', '')
    # 强制更新
    force = request.args.get('force', '')
    force = 0 if not force or force == '0' else 1

    # 初始化数据
    return_dic = {}
    goods_id = goods_url.split('id=', 1)[1].split('&', 1)[0]
    if not goods_id:
        return_dic['result'] = 1
        return_dic['msg'] = '未输入goods_url，请重新输入'
        return_dic['data'] = ''
        return json.dumps(return_dic), 200

    result = {}
    if not force:
        result = TaobaoGoodsResult().find_complete_goods(goods_id)
    if result:
        return_dic['result'] = 0
        return_dic['msg'] = '已获取商品:{}的详情'.format(goods_url)
        goods = result.get('result')
        for _key in ['sku', 'polling_img', 'des_image', 'goods_attr_list']:
            if _key in goods and goods[_key] and isinstance(goods[_key], str):
                goods[_key] = json.loads(goods[_key])
        if 'content' in goods:
            goods.pop('content')
        return_dic['data'] = goods
    # 如果没有商品可以返回，就入库爬取
    else:
        priority = 0
        if 'icy.design' in callback_link:
            priority = 3
        elif force:
            priority = 2
        elif callback_link:
            priority = 1
        GoodsDetails(goods_url, callback_link=callback_link, priority=priority).enqueue()
        return_dic['result'] = 0
        return_dic['msg'] = "开始抓取: {}, 优先级：{}".format(goods_url, priority)
        return_dic['callback_link'] = "callback_link: ({})".format(callback_link)
    return json.dumps(return_dic), 200


@app.route('/apis/crawl_taobao_shop/all-goods-suspend', methods=['GET'])
def crawl_taobao_goods_shop_goods():
    """
    获取第三方商品店铺下的所有商品ID
    暂停这个接口
    :return:
    """
    # 商品ID
    shop_id = request.args.get('shop_id', '')
    # 页码数
    page = int(request.args.get('page', 1))
    page = page - 1 if page > 0 else 0
    # 分页每页大小
    page_size = int(request.args.get('page_size', 20))
    # 回调链接
    callback_link = request.args.get('callback_link', '')

    # 初始化数据
    return_dic = {}

    if not shop_id:
        return_dic['result'] = 1
        return_dic['msg'] = '未传入shop ID:{}，请重新输入'.format(shop_id)
        return json.dumps(return_dic), 200

    goods = TaobaoGoodsResult().find_all_goods(shop_id=shop_id)
    if goods.count() < 1:
        url = 'https://shop{}.taobao.com/'.format(shop_id)
        ShopDetails(url, callback_link=callback_link).enqueue()
        return_dic['result'] = 1
        return_dic['msg'] = '没有此店铺:{}的商品详情, 注册之'.format(shop_id)
    else:
        goods_id_list = []
        return_dic['result'] = 0
        return_dic['msg'] = '获取了店铺:{}的商品详情'.format(shop_id)
        all_goods = goods.skip(page * page_size).limit(page_size)
        for g in all_goods:
            goods_id_list.append(g.get('result').get('goods_id'))
        return_dic['data'] = {
            'goods_ids': goods_id_list
        }

    return json.dumps(return_dic), 200


@app.route('/apis/tianmao/shop', methods=['POST'])
def tianmao_shop():
    """
    天猫店铺【注册】的接口
    :return:
    """
    # 店铺 URL
    shop_url = request.args.get('shop_url', '')

    # 初始化数据
    return_dic = {}

    if request.method == 'POST':
        if shop_url:
            shop_url = shop_url.split('tmall.com', 1)[0] + 'tmall.com'
            shop = TianMao().find({
                'result.shop_url': shop_url,
                'result.shop_type': {'$exists': 'true'},
            })
            if shop.count() < 1:
                tm_handler().parse_tmall_shop(shop_url)
                return_dic['result'] = 0
                return_dic['msg'] = '没有此店铺:{}, 注册之'.format(shop_url)
            else:
                return_dic['result'] = 1
                return_dic['msg'] = '已有店铺:{}'.format(shop_url)
        else:
            return_dic['result'] = 1
            return_dic['msg'] = '未传入 shop_url:{}，请重新输入'.format(shop_url)
    else:
        return_dic['result'] = 0
        return_dic['msg'] = '非 POST 请求，获取不到数据'
    return json.dumps(return_dic), 200


@app.route('/apis/tianmao/goods', methods=["GET"])
def tianmao_goods():
    """
    天猫【商品详情】的获取接口
    :return:
    """
    # 店铺 URL
    goods_id = request.args.get('goods_id', '')
    goods_url = request.args.get('goods_url', '')
    shop_type = int(request.args.get('shop_type', 2))
    callback = request.args.get('callback', '')

    # 初始化数据
    return_dic = {}

    # 获取商品的真实 URL
    if goods_url:
        goods_url = goods_url
    elif goods_id:
        if str(shop_type) == '1':
            # 淘宝
            goods_url = 'https://item.taobao.com/item.htm?id={}'.format(goods_id)
        elif str(shop_type) == '2':
            # 天猫
            goods_url = 'https://detail.tmall.com/item.htm?id={}'.format(goods_id)
        else:
            # 输入shopType不合格
            return_dic['result'] = 1
            return_dic['msg'] = "输入的店铺类型: shop_type 不合格，请重新输入"
            return json.dumps(return_dic), 200
    else:
        return_dic['result'] = 1
        return_dic['msg'] = "请传入商品ID和商品链接中的任意一个"
        return json.dumps(return_dic), 200

    if request.method == 'POST':
        return_dic['result'] = 1
        return_dic['msg'] = '没有post'
    else:
        if goods_url or goods_id:
            # 获取商品详情
            goods_details = {}
            goods_id = goods_url.split('id=')[1].split('&')[0] or goods_id
            goods = TianMao().find_one({
                'result.goods_id': goods_id,
                'result.off_shelf': {'$exists': 'true'},
            })
            if goods is None:
                Queue('tianmao:goods-details', host='pyspider-redis').put(goods_url + ';' + callback)
                return_dic['result'] = 0
                return_dic['msg'] = "商品:{} 不在数据库中，注册之。".format(goods_id)
            else:
                goods_details['goods_id'] = goods.get('result').get('goods_id')
                goods_details['shop_id'] = goods.get('result').get('shop_id')
                goods_details['goods_name'] = goods.get('result').get('goods_name')
                goods_details['shop_dynamic_score'] = goods.get('result').get('shop_dynamic_score')
                goods_details['pre_view_pic'] = goods.get('result').get('pre_view_pic')
                return_dic['result'] = 0
                return_dic['msg'] = "商品:{} 已经在数据库中。".format(goods_id)
                return_dic['data'] = goods_details
        else:
            return_dic['result'] = 1
            return_dic['msg'] = '未传入 goods_id:{}，请重新输入'.format(goods_id)
    return json.dumps(return_dic), 200


@app.route('/apis/weipinhui/goods')
def weipinhui_goods():
    """
    唯品会【商品详情】的获取接口
    :return:
    """
    # 店铺 URL
    goods_date = request.args.get('goods_date', '')

    # 初始化数据
    return_dic = {}

    # 获取商品的 json 数据详情
    if goods_date:
        goods = Weipinhui().bulk()
        if str(goods) == '1':
            pass
        else:
            # 输入shopType不合格
            return_dic['result'] = 1
            return_dic['msg'] = "输入的店铺类型: shop_type 不合格，请重新输入"
            return json.dumps(return_dic), 200
    else:
        return_dic['result'] = 1
        return_dic['msg'] = "请传入商品ID和商品链接中的任意一个"
        return json.dumps(return_dic), 200

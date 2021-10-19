import colorsys
import json
import io
from copy import deepcopy

import fire
import requests
import time

from blog_spider.config import *
from blog_spider.model.es.blog_result import BlogResult
from blog_spider.model.es.blogger_msg import BlogMsg
from blog_spider.model.result import Result
from blog_spider.model.task import Task
from blog_spider.page.blog_image_download import BlogImgDown
from blog_spider.page.ins_blogger import InsBlogger
from blog_spider.page.weibo_blogger_id import WeiboBloggerId
from blog_spider.page.weibo_blogger_id_result import WeiboBloggerIdRlt
from pyspider.helper.date import Date
from pyspider.helper.logging import processor_logger
from pyspider.helper.string import merge_str
from pyspider.libs.oss import oss_cdn
from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True


class Cron:
    def update_blogger_article(self, account_type, status=1):
        """
        更新博主发的内容
        频率：4个小时
        :param account_type: 1，weibo；2，ins；
        :param status: 2：关闭; 1：开启
        :return:
        """
        # content_type 是用来区分博主内容和关键词内容的
        content_type = 1

        if int(account_type) == 1:
            # 抓取微博内容
            bloggers = BlogMsg().get_active_content(account_type, status)
            for blogger in bloggers:
                for _blog in blogger:
                    account_key = _blog['account_key']
                    keywords = _blog.get('keywords')
                    queue_data = {
                        "type": account_type,
                        "accountKey": account_key,
                        "keywords": keywords,
                        "status": status,
                        "contentType": content_type,
                    }
                    WeiboBloggerId(account_key, priority=PRIORITY_FIRST, to_next_page=True,
                                   queue_data=queue_data).enqueue()

                    # 发送抓取通知
                    self._send_update_inform(account_type, account_key)
        elif int(account_type) == 2:
            # 抓取 ins 内容
            pass

    def send_finished_data(self, data_type=1, repair=0):
        """
        发送已更新的数据到服务端
        :param data_type: 1, 博主; 2, 搜索词
        :param repair: 1, 修复脚本; 0, 正常脚本
        :return:
        """
        from mq_handler import CONST_MESSAGE_TAG_BLOG_RESULT, CONST_ACTION_UPDATE
        from pyspider.libs.mq import MQ
        if repair:
            repair_status = True
        else:
            repair_status = False
        if data_type == 1:
            is_blogger = True
            status = 1
        else:
            is_blogger = False
            status = 2
        recent_time = Date.now().plus_hours(-UPDATE_HOUR - 24 * 5).timestamp()
        search_key = ''
        all_blogs = BlogResult().get_blog_content(search_key, recent_time, is_blogger, image_crawled=True,
                                                  server_sended=False, page_size=50, status=status,
                                                  repair=repair_status)

        for _rlist in all_blogs:
            # 分批发送已抓取完的数据到服务端
            return_list = list()
            # 更新es的数据
            return_es_list = list()
            for _r in _rlist:
                try:
                    filter_dict = dict()
                    filter_dict['type'] = _r.get('data_type')
                    filter_dict['accountKey'] = _r.get('account_key')
                    filter_dict['name'] = _r.get('name')
                    filter_dict['sex'] = _r.get('sex')
                    filter_dict['avatar'] = _r.get('avatar')
                    if filter_dict['avatar'].get('avatar_img'):
                        filter_dict['avatar'].pop('avatar_img')
                    filter_dict['avatar'].pop('img_saved')
                    filter_dict['contentId'] = _r.get('content_id')
                    filter_dict['content'] = _r.get('content')
                    filter_dict['images'] = _r.get('images')
                    for _img in filter_dict['images']:
                        if _img.get('path'):
                            _img.pop('path')
                        _img.pop('img_saved')
                    filter_dict['publishTime'] = _r.get('publish_time')
                    filter_dict['createTime'] = _r.get('create_time')
                    filter_dict['keywords'] = _r.get('keywords')
                    filter_dict['contentType'] = _r.get('content_type')
                    filter_dict['repair'] = repair_status
                    return_list.append(filter_dict)

                    update_es_dict = dict()
                    update_es_dict['content_id'] = _r.get('content_id')
                    update_es_dict['server_sended'] = True
                    return_es_list.append(update_es_dict)
                except Exception as e:
                    processor_logger.exception('send finished image information exception: {}'.format(e))
            msg_tag = CONST_MESSAGE_TAG_BLOG_RESULT
            return_date = Date.now().format()
            MQ().publish_message(msg_tag, return_list, recent_time, return_date, CONST_ACTION_UPDATE)

            # 更新已经发送的数据
            BlogResult().update(return_es_list, async=True)

    def update_article_image(self, account_key=0):
        """
        这个是修补数据, 抓取没抓成功的图片;
        更新未被抓取的图片信息;
        只发送已经更新完图片的内容通知
        :param account_type: 1，weibo；2，ins；
        :param status: 1：开启; 2：关闭;
        :param account_key: 更新指定用户的信息
        :return:
        """
        recent_time = Date.now().plus_hours(-UPDATE_HOUR - 24 * 5).timestamp()
        is_blogger_list = [True, False]
        search_key = ''
        account_type = 0
        status = 0
        for is_blogger in is_blogger_list:
            all_blogs = BlogResult().get_blog_content(search_key, recent_time, is_blogger, image_crawled=False,
                                                      server_sended=False, status=status, account_type=account_type,
                                                      page_size=10, account_key=int(account_key))
            for _blog in all_blogs:
                send_es_list = list()
                for _b in _blog:
                    try:
                        content_id = _b['content_id']

                        # 如果有没有图片内容变动，则不发送es更新消息
                        send_es_update = False
                        status_flag = True
                        # 如果所有的图片状态都为True, 标记图片为已抓取, 否则置为False
                        image_flag = True
                        # 要被更新的内容
                        update_data = dict()
                        # 头像信息
                        avatar_status = _b['avatar'].get('img_saved')
                        image_path = _b['avatar'].get('image')
                        avatar_img = _b['avatar'].get('avatar_img')

                        # 判断抓取状态
                        if not avatar_status:
                            status_flag = False
                            if oss_cdn.is_had(image_path):
                                # oss 有数据，更新图片的信息
                                img_data = Image.open(io.BytesIO(oss_cdn.get_data(image_path)))
                                width, height = img_data.size
                                avatar_status = True
                                send_es_update = True

                                update_data['avatar'] = dict()
                                update_data['avatar']['image'] = image_path
                                update_data['avatar']['avatar_img'] = avatar_img
                                update_data['avatar']['width'] = width
                                update_data['avatar']['height'] = height
                                update_data['avatar']['img_saved'] = avatar_status
                            else:
                                # oss 没有数据, 发送抓取请求
                                image_flag = False
                                if avatar_img:
                                    if account_key:
                                        priority = PRIORITY_HIGHEST
                                    else:
                                        priority = PRIORITY_FIRST
                                    task_id = merge_str(avatar_img.split('/')[-1])
                                    if not self._in_task(task_id):
                                        BlogImgDown(avatar_img, image_path, priority=priority).enqueue()

                        # 内容图片信息
                        images_update_data = list()
                        for _img in _b['images']:
                            img_status = _img.get('img_saved')
                            img_path = _img.get('image')
                            image_url = _img.get('path')

                            images_inner_data = deepcopy(_img)

                            # 判断抓取状态
                            if not img_status:
                                status_flag = False
                                if oss_cdn.is_had(img_path):
                                    # oss 有数据，更新图片的信息
                                    imgs_data = Image.open(io.BytesIO(oss_cdn.get_data(img_path)))
                                    imgs_width, imgs_height = imgs_data.size
                                    # rgb_imgs = imgs_data.convert('RGB')
                                    # color = self._get_image_digix((imgs_width, imgs_height), rgb_imgs)
                                    # color = self._get_image_digix_by_qiniu(img_path)
                                    # if not color:
                                    #     continue
                                    color = "#FFFFFF"
                                    img_status = True
                                    send_es_update = True

                                    images_inner_data['width'] = imgs_width
                                    images_inner_data['height'] = imgs_height
                                    images_inner_data['imageColor'] = color
                                    images_inner_data['img_saved'] = img_status
                                else:
                                    image_flag = False
                                    # oss 没有数据, 发送抓取请求
                                    if image_url:
                                        if account_key:
                                            priority = PRIORITY_HIGHEST
                                        else:
                                            priority = PRIORITY_FIRST
                                        task_id = merge_str(image_url.split('/')[-1])
                                        if not self._in_task(task_id):
                                            BlogImgDown(image_url, img_path, priority=priority).enqueue()
                            images_update_data.append(images_inner_data)
                        # 如果图片全部被抓完了，就更新图片抓取状态
                        if image_flag:
                            update_data['image_crawled'] = image_flag
                        update_data['images'] = images_update_data
                        update_data['content_id'] = content_id
                        if send_es_update or status_flag:
                            send_es_list.append(update_data)
                    except Exception as e:
                        processor_logger.exception('catch image information exception: {}'.format(e))
                if send_es_list:
                    BlogResult().update(send_es_list, async=True)

    def update_content_by_blogger(self, account_key):
        """
        手动更新博主的所有消息
        :param account_key:
        :return:
        """
        queue_data = {
            "type": 1,
            "accountKey": account_key,
            "status": 1
        }
        WeiboBloggerIdRlt(account_key, to_next_page=True, queue_data=queue_data).get_result()

    def repair_img_script(self):
        """
        修复被覆盖掉图片信息的内容
        :return:
        """
        recent_time = Date.now().plus_hours(-UPDATE_HOUR - 24 * 5).timestamp()
        search_key = ''
        is_blogger = True
        status = 1
        repair = ''
        all_blogs = BlogResult().get_blog_content(search_key, recent_time, is_blogger, image_crawled=True,
                                                  server_sended=True, page_size=50, status=status, repair=repair,
                                                  images_null=True)
        for _blog in all_blogs:
            send_es_list = list()
            for _b in _blog:
                return_es_dict = dict()
                content_id = _b['content_id']
                task_id = '{}:30'.format(content_id)
                images = Result().find_one({'taskid': task_id})
                image_list = images['result']['preview_data']['images'] if images else []
                if image_list:
                    return_es_dict['content_id'] = content_id
                    return_es_dict['images'] = image_list
                    return_es_dict['repair'] = True
                    send_es_list.append(return_es_dict)
            BlogResult().update(send_es_list, async=True)

    def cdn_warm(self):
        """
        爬虫图片，进行cdn预热
        用七牛的fetch接口从阿里云oss拉图片（如果正常回源会占用线上带宽）
        :return:
        """
        from pyspider.helper.es_query_builder import EsQueryBuilder
        from concurrent import futures
        from qiniu import Auth
        from qiniu import BucketManager
        from pyspider.config import config
        access_key = config.get('qiniu', 'access_key')
        secret_key = config.get('qiniu', 'secret_key')
        bucket_name = config.get('qiniu', 'bucket_name')
        bucket = BucketManager(Auth(access_key, secret_key))
        executor = futures.ThreadPoolExecutor(max_workers=10)

        def get_image_url(path):
            url = 'https://yourdream-images.oss-cn-beijing.aliyuncs.com/' + path
            return url

        def warm(path):
            return path, bucket.fetch(get_image_url(path), bucket_name, path)

        for _list in BlogResult().scroll(
                EsQueryBuilder()
                        .term('image_crawled', True)
                        .must_not(EsQueryBuilder().term('cdnWarmed', 1))
                        .source(['images', 'content_id', 'avatar']),
                print_progress=True,
                scroll='10m',
                page_size=50
        ):
            docs = []
            urls = []
            for _ in _list:
                _path = _.get('avatar', {}).get('image')
                if _path:
                    urls.append(_path)
                _images = _.get('images', [])
                if _images and isinstance(_images, list):
                    for _image in _images:
                        _path = _image.get('image')
                        if _path:
                            urls.append(_path)
                docs.append({'content_id': _['content_id'], 'cdnWarmed': 1})
            results = executor.map(warm, urls)
            for i, result in enumerate(results):
                print(result)
            BlogResult().update(docs)

    def repair_account_msg(self):
        """
        把博主信息迁移到博主信息专用index
        :return:
        """
        account_list = BlogResult().get_all_blogger_msg()
        new_list = list()
        for account in account_list:
            account['content_type'] = 1
            new_list.append(account)
        BlogMsg().update(new_list, async=True)

    def repair_blog_image(self):
        """
        爬虫抓取的博主头像地址带有参数，会导致前端拿不到图片；
        修复这个bug，找出所有带有参数的图片，删除url带有的参数
        :return:
        """
        de_duplicate_list = []
        for result in BlogResult().get_all_blog_content_flexible(server_sended=1):
            image_update = []
            for data in result:
                avatar = data['avatar']
                content_id = data['content_id']
                image_split_words = ''
                if '.jpg' in avatar['avatar_img']:
                    avatar_img_split = avatar['avatar_img'].split('.jpg', 1)
                    image_split_words = '.jpg'
                elif '.gif' in avatar['avatar_img']:
                    avatar_img_split = avatar['avatar_img'].split('.gif', 1)
                    image_split_words = '.gif'
                else:
                    avatar_img_split = avatar['avatar_img'].split('.jpeg', 1)
                    image_split_words = '.jpeg'

                print('content_id', content_id)
                if avatar_img_split[1]:
                    avatar_img = avatar_img_split[0] + image_split_words
                    avatar_img_path = oss_cdn.get_key(oss_cdn.CONST_BLOG_IMAGE + '{}/'.format(content_id),
                                                      avatar_img.split('/')[-1])

                    # 拿到图片之后，判断oss里有没有，没有就上传到oss，有的话就加热
                    if oss_cdn.is_had(avatar_img_path):
                        # oss 有数据，更新图片的信息
                        print('oss 有数据，更新图片的信息')
                        oss_cdn.get_data(avatar_img_path)
                    else:
                        # oss 没有数据, 发送抓取请求,
                        print('oss 没有数据, 发送抓取请求,')
                        task_id = merge_str(avatar_img.split('/')[-1])
                        if not self._in_task(task_id):
                            BlogImgDown(avatar_img, avatar_img_path, priority=PRIORITY_FIRST).enqueue()

                    de_duplicate_list.append(avatar_img)

                    # 更新用户的头像信息
                    blog_dict = {}
                    avatar_dict = {}
                    avatar_dict['image'] = avatar_img_path
                    avatar_dict['avatar_img'] = avatar_img
                    avatar_dict['width'] = avatar['width']
                    avatar_dict['height'] = avatar['height']
                    avatar_dict['img_saved'] = avatar['img_saved']
                    blog_dict['content_id'] = content_id
                    blog_dict['avatar'] = avatar_dict
                    image_update.append(blog_dict)
            BlogResult().update(image_update, async=True)
        print('本次修复的头像url的数量:', len(de_duplicate_list))

    def consume_ins_blogger(self, account_key):
        """
        消费ins的博主信息
        :param account_key:
        :return:
        """
        account_key = 'jupppal'
        InsBlogger(account_key).entry()

    def consume_ins_keywords(self, keyword):
        """
        消费ins的关键字
        :param keyword:
        :return:
        """
        pass

    def fix_keywords_article(self, fix):
        """
        临时修复带关键词的博主内容没有带上关键词
        :param fix: 为1，则开始修复数据，2：发送修复过的数据
        :return:
        """
        if fix == 1:
            bloggers = BlogMsg().get_active_content(keywords=1)
            for _blog in bloggers:
                for _b in _blog:
                    account_key = _b['account_key']
                    keywords = _b['keywords']
                    print('account_key: {}'.format(account_key))
                    print('keywords: {}'.format(keywords))

                    # 修复博客的数据
                    article_list = list()
                    articles = BlogResult().get_one_blogger_content(account_key, get_all=True)
                    for article in articles:
                        for _ar in article:
                            ar_dict = dict()
                            keywords_list = list()
                            content_id = _ar['content_id']
                            content = _ar['content']

                            # 获取匹配的关键词
                            for _k in keywords:
                                _k = _k.strip()
                                if _k in content:
                                    keywords_list.append(_k)

                            repair = True
                            ar_dict['content_id'] = content_id
                            ar_dict['keywords'] = keywords_list
                            ar_dict['repair'] = repair
                            article_list.append(ar_dict)

                    # 发送更新数据
                    BlogResult().update(article_list, async=True)
                    time.sleep(5)
        elif fix == 2:
            bloggers = BlogMsg().get_active_content(keywords=1)
            for _blog in bloggers:

                for _b in _blog:
                    account_key = _b['account_key']
                    keywords = _b['keywords']
                    print('account_key: {}'.format(account_key))
                    print('keywords: {}'.format(keywords))

                    articles = BlogResult().get_one_blogger_content(account_key, get_all=True, image_crawled=1)
                    for article in articles:
                        # 分批发送已抓取完的数据到服务
                        return_list = list()
                        # 更新es的数据
                        return_es_list = list()
                        for _r in article:
                            try:
                                filter_dict = dict()
                                filter_dict['type'] = _r.get('data_type')
                                filter_dict['accountKey'] = _r.get('account_key')
                                filter_dict['name'] = _r.get('name')
                                filter_dict['sex'] = _r.get('sex')
                                filter_dict['avatar'] = _r.get('avatar')
                                if filter_dict['avatar'].get('avatar_img'):
                                    filter_dict['avatar'].pop('avatar_img')
                                filter_dict['avatar'].pop('img_saved')
                                filter_dict['contentId'] = _r.get('content_id')
                                filter_dict['content'] = _r.get('content')
                                filter_dict['images'] = _r.get('images')
                                for _img in filter_dict['images']:
                                    if _img.get('path'):
                                        _img.pop('path')
                                    _img.pop('img_saved')
                                filter_dict['publishTime'] = _r.get('publish_time')
                                filter_dict['createTime'] = _r.get('create_time')
                                filter_dict['keywords'] = _r.get('keywords')
                                filter_dict['contentType'] = _r.get('content_type', 1)
                                filter_dict['repair'] = _r.get('repair')
                                return_list.append(filter_dict)

                                update_es_dict = dict()
                                update_es_dict['content_id'] = _r.get('content_id')
                                update_es_dict['server_sended'] = True
                                return_es_list.append(update_es_dict)
                            except Exception as e:
                                processor_logger.exception('send finished image information exception: {}'.format(e))
                        time.sleep(10)
                        from mq_handler import CONST_MESSAGE_TAG_BLOG_RESULT
                        from pyspider.libs.mq import MQ
                        from mq_handler import CONST_ACTION_UPDATE
                        msg_tag = CONST_MESSAGE_TAG_BLOG_RESULT
                        return_date = Date.now().format()
                        MQ().publish_message(msg_tag, return_list, 'repair', return_date, CONST_ACTION_UPDATE)

                        # 更新已经发送的数据
                        BlogResult().update(return_es_list, async=True)

    def _in_task(self, task_id):
        my_task_id = Task().find_one({'taskid': task_id})
        st_id = my_task_id.get('status') if my_task_id else 0
        if st_id == 1:
            # 在队列中
            return True
        else:
            return False

    def _get_image_digix(self, size, rgb_img):
        """
        获取图片的平均 RGB 颜色值
        :param size: (width, height) 图片的宽高值
        :param rgb_img: PIL 的 RGB 对象
        :return:
        """
        width, height = size
        width_step = int(width / 6)
        height_step = int(height / 6)
        r = 0
        g = 0
        b = 0
        for w in range(0, width, width_step):
            for h in range(0, height, height_step):
                _r, _g, _b = rgb_img.getpixel((w, h))
                r += _r
                g += _g
                b += _b

        color_digit = '#%02x%02x%02x' % (int(r / 36), int(g / 36), int(b / 36))
        return color_digit

    def _get_image_digix_two(self, image):
        """
        另外一种获取图片主要色值的算法
        :param image:
        :return:
        """
        image = image.convert('RGBA')
        image.thumbnail((200, 200))

        max_score = 0
        dominant_color = None

        for count, (r, g, b, a) in image.getcolors(image.size[0] * image.size[1]):
            # 跳过纯黑色
            if a == 0:
                continue

            saturation = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)[1]
            y = min(abs(r * 2104 + g * 4130 + b * 802 + 4096 + 131072) >> 13, 235)
            y = (y - 16.0) / (235 - 16)

            # 忽略高亮色
            if y > 0.9:
                continue

            # Calculate the score, preferring highly saturated colors.
            # Add 0.1 to the saturation so we don't completely ignore grayscale
            # colors by multiplying the count by zero, but still give them a low
            # weight.
            score = (saturation + 0.1) * count

            if score > max_score:
                max_score = score
                dominant_color = (r, g, b)

        color_digit = '#%02x%02x%02x' % dominant_color if dominant_color else None
        return color_digit

    def _get_image_digix_by_qiniu(self, image_path, retry=1):
        """
        使用七牛的图片平均色值接口
        :param image_path:
        :return:
        """
        try:
            url = 'http://image3.ichuanyi.cn/{}?imageAve'.format(image_path)
            headers = {
                'User-Agent': USER_AGENT,
                'Host': 'image3.ichuanyi.cn'
            }
            rgb = requests.get(url, headers=headers, timeout=3).json().get('RGB')
            rgb = '#' + rgb.replace('0x', '')
            return rgb
        except Exception as e:
            processor_logger.error('parse qiniu image error:{}'.format(e))
            if retry > 0:
                self._get_image_digix_by_qiniu(image_path, retry - 1)
            else:
                return ''

    def _send_update_inform(self, account_type, account_key):
        """
        发送抓取每个博主的更新信息
        :param account_type:
        :param account_key:
        :return:
        """
        from mq_handler import CONST_MESSAGE_TAG_BLOG_UP_INFORM, CONST_ACTION_UPDATE
        from pyspider.libs.mq import MQ
        now = Date.now().format()
        return_msg = {
            "type": account_type,  # 1 weibo 2 ins
            "accountKey": account_key,
            "lastUpdateTime": now,
        }
        msg_tag = CONST_MESSAGE_TAG_BLOG_UP_INFORM
        return_date = now
        MQ().publish_message(msg_tag, return_msg, account_key, return_date, CONST_ACTION_UPDATE)


if __name__ == '__main__':
    fire.Fire(Cron)

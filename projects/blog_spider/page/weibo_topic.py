import json

from blog_spider.config import *
from blog_spider.model.es.blog_result import BlogResult
from blog_spider.page.blog_image_download import BlogImgDown
from blog_spider.page.weibo_article import WeiboArticle
from pyspider.helper.string import merge_str
from pyspider.libs.base_crawl import *
from pyspider.helper.ips_pool import IpsPool
from pyspider.helper.date import Date
from pyspider.libs.oss import oss_cdn


class WeiboTopic(BaseCrawl):
    """
    抓取微博的帖子内容；
    每个话题抓最多300个
    图片统一存到oss；
    """

    URL = 'https://m.weibo.cn/api/container/getIndex?containerid=100103type%3D63%26q%3D{words}&page_type=searchall&' \
          'page={page}'

    def __init__(self, search_words, page=1, use_proxy=True, priority=0, to_next_page=False, queue_data=''):
        super(WeiboTopic, self).__init__()
        self.__priority = priority
        self.__search_words = search_words
        self.__page = page
        self.__use_proxy = use_proxy
        self.__to_next_page = to_next_page
        self.__queue_data = queue_data

    def crawl_builder(self):
        builder = CrawlBuilder() \
            .set_url(self.URL.format(words=self.__search_words, page=self.__page)) \
            .set_headers_kv('User-Agent', USER_AGENT) \
            .schedule_priority(self.__priority) \
            .set_timeout(GOODS_TIMEOUT) \
            .set_connect_timeout(GOODS_CONNECT_TIMEOUT) \
            .set_task_id(merge_str(self.__search_words, self.__page))

        if self.__use_proxy:
            builder.set_proxy(IpsPool.get_ip_from_pool())

        return builder

    def parse_response(self, response, task):
        text = response.text
        js_data = json.loads(text)
        cards = js_data['data']['cards']
        if cards:
            # 爬虫结果类型
            data_type = self.__queue_data.get('type')  # weibo
            # 图片是否已经全部都抓完了
            image_crawled = False
            # 是否已经把这条内容发给服务端了
            server_sended = False

            for _card in cards:
                if not _card.get('card_group'):
                    continue
                for card_group in _card['card_group']:
                    elements = ['left_element', 'right_element']
                    for elem in elements:
                        card_data = card_group.get(elem)
                        if not card_data or not isinstance(card_data, dict):
                            continue
                        mblog = card_data.get('mblog')
                        if not mblog:
                            continue
                        # 标记博主
                        is_blogger = False
                        # 内容ID
                        content_id = mblog['id']
                        # 如果存在该博客内容，跳过
                        if BlogResult().exists(content_id):
                            continue
                        # 用户的唯一标识
                        account_key = mblog['user']['id']
                        # 用户的用户名
                        name = mblog['user']['screen_name']
                        # 用户的性别
                        sex = mblog['user']['gender']
                        # 用户的头像
                        avatar = dict()
                        if '.jpg' in mblog['user']['profile_image_url']:
                            avatar_img = mblog['user']['profile_image_url'].split('.jpg', 1)[0] + '.jpg'
                        elif '.gif' in mblog['user']['profile_image_url']:
                            avatar_img = mblog['user']['profile_image_url'].split('.gif', 1)[0] + '.gif'
                        else:
                            avatar_img = mblog['user']['profile_image_url'].split('.jpeg', 1)[0] + '.jpeg'
                        avatar_img_path = oss_cdn.get_key(oss_cdn.CONST_BLOG_IMAGE + '{}/'.format(content_id),
                                                          avatar_img.split('/')[-1])
                        avatar['image'] = avatar_img_path
                        avatar['avatar_img'] = avatar_img
                        avatar['width'] = 0
                        avatar['height'] = 0
                        avatar['img_saved'] = False
                        self.crawl_handler_page(BlogImgDown(avatar_img, avatar_img_path, priority=self.__priority))
                        # 用户是否是蓝v
                        blue_v_list = [1, 2, 3, 5]
                        blue_vip = True if int(mblog['user']['verified_type']) in blue_v_list else False
                        # 具体内容
                        content = mblog['text']
                        # 完整的内容的链接
                        full_content_url = 'https://m.weibo.cn/detail/{}'.format(content_id)
                        # 内容里的图片地址
                        images = list()
                        img_data = mblog.get('pics')
                        if img_data:
                            for _img in img_data:
                                img_dict = dict()
                                img_url = _img['large']['url']
                                img_path = oss_cdn.get_key(oss_cdn.CONST_BLOG_IMAGE + '{}/'.format(content_id),
                                                           img_url.split('/')[-1])
                                img_dict['image'] = img_path
                                img_geo = _img['large'].get('geo')
                                img_dict['width'] = img_geo['width'] if isinstance(img_geo, dict) else ''
                                img_dict['height'] = img_geo['height'] if isinstance(img_geo, dict) else ''
                                img_dict['imageColor'] = '#FFFFFF'
                                img_dict['path'] = _img['large']['url']
                                img_dict['img_saved'] = False
                                self.crawl_handler_page(BlogImgDown(img_url, img_path, priority=self.__priority))
                                images.append(img_dict)
                        # 第三方发布时间
                        publish_time_str = mblog['created_at']
                        if '分钟前' in publish_time_str:
                            publish_time_min = int(publish_time_str.split('分钟前', 1)[0].strip())
                            publish_time = Date.now().plus_minutes(-publish_time_min).format()
                        elif '小时前' in publish_time_str:
                            publish_time_hour = int(publish_time_str.split('小时前', 1)[0].strip())
                            publish_time = Date.now().plus_hours(-publish_time_hour).format()
                        elif '今天' in publish_time_str:
                            publish_time_to = publish_time_str.split('今天', 1)[1].strip()
                            publish_time = Date.now().format(full=False) + publish_time_to + ':00'
                        elif '昨天' in publish_time_str:
                            publish_time_yes = publish_time_str.split('昨天', 1)[1].strip()
                            publish_time = Date.now().plus_days(-1).format(full=False) + publish_time_yes + ':00'
                        elif len(publish_time_str.split('-')) == 2:
                            publish_time = Date.now().strftime('%Y') + '-{}'.format(publish_time_str)
                        else:
                            publish_time = publish_time_str
                        # 爬虫抓取时间
                        create_time = Date.now().timestamp()
                        # 关键词
                        keywords = [self.__search_words]

                        article_data = {
                            'data_type': data_type,
                            'image_crawled': image_crawled,
                            'server_sended': server_sended,
                            'account_key': account_key,
                            'name': name,
                            'sex': sex,
                            'avatar': avatar,
                            'content_id': content_id,
                            'content': content,
                            'images': images,
                            'publish_time': publish_time,
                            'create_time': create_time,
                            'keywords': keywords,
                            'full_content_url': full_content_url,
                            'blue_vip': blue_vip,
                            'is_blogger': is_blogger,
                            'status': self.__queue_data.get('status', 2),
                            'content_type': self.__queue_data.get('contentType'),
                        }
                        if not blue_vip:
                            self.crawl_handler_page(
                                WeiboArticle(full_content_url, article_data, use_proxy=True, priority=self.__priority))

            if self.__page < KEY_WORD_MAX_PAGE and self.__to_next_page:
                self.crawl_handler_page(
                    WeiboTopic(self.__search_words, self.__page + 1, self.__use_proxy, self.__priority,
                               self.__to_next_page, self.__queue_data))
            else:
                # self.send_inform()
                pass
        else:
            # self.send_inform()
            pass
        return {
            'unique_name': 'weibo_topic_tag',
            'content': text
        }

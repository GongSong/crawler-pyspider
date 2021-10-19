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


class WeiboBlogger(BaseCrawl):
    """
    抓取微博博主发的微博
    """

    def __init__(self, url, use_proxy=True, priority=0, page=1, to_next_page=False, queue_data=''):
        super(WeiboBlogger, self).__init__()
        self.__priority = priority
        self.__url = url
        self.__catch_url = self.__url + '&page={}'.format(page)
        self.__use_proxy = use_proxy
        self.__page = page
        self.__to_next_page = to_next_page
        self.__queue_data = queue_data

    def crawl_builder(self):
        builder = CrawlBuilder() \
            .set_url(self.__catch_url) \
            .set_headers_kv('User-Agent', USER_AGENT) \
            .schedule_priority(self.__priority) \
            .set_task_id(merge_str(self.__url[-16:], self.__page))

        if self.__use_proxy:
            builder.set_proxy(IpsPool.get_ip_from_pool())

        return builder

    def parse_response(self, response, task):
        text = response.text
        js_data = json.loads(text)
        cards = js_data['data']['cards']
        if cards:
            # 爬虫结果类型
            data_type = self.__queue_data.get("type")  # weibo
            # 关键词
            keywords = self.__queue_data.get('keywords', [])
            # 图片是否已经全部都抓完了
            image_crawled = False
            # 是否已经把这条内容发给服务端了
            server_sended = False

            for _card in cards:
                mblog = _card.get('mblog')
                if not mblog:
                    continue
                # 跳过转发的和有视频的内容
                if mblog.get('raw_text') or mblog.get('obj_ext'):
                    # raw_text 是转发时带的内容，代表转发，obj_ext 是观看次数，代表视频内容
                    continue
                # 标记博主
                is_blogger = True
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
                blue_v_list = [1, 2, 3, 4, 5]
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
                        img_dict['path'] = img_url
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
                    publish_time = Date.now().format(full=False) + ' {}:00'.format(publish_time_to)
                elif '昨天' in publish_time_str:
                    publish_time_yes = publish_time_str.split('昨天', 1)[1].strip()
                    publish_time = Date.now().plus_days(-1).format(full=False) + ' {}:00'.format(publish_time_yes)
                elif len(publish_time_str.split('-')) == 2:
                    publish_time = Date.now().strftime('%Y') + '-{}'.format(publish_time_str.strip())
                else:
                    publish_time = publish_time_str.strip()
                publish_time = Date(publish_time).format_es_utc()
                # 爬虫抓取时间
                create_time = Date.now().timestamp()

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
                # 过滤除了指定用户抓取的蓝v
                if not blue_vip or int(self.__queue_data.get('contentType', 0)) == 1:
                    self.crawl_handler_page(
                        WeiboArticle(full_content_url, article_data, use_proxy=True, priority=self.__priority))

            if self.__page < BLOGGER_MAX_PAGE and self.__to_next_page:
                self.crawl_handler_page(
                    WeiboBlogger(self.__url, page=self.__page + 1, use_proxy=self.__use_proxy, priority=self.__priority,
                                 to_next_page=self.__to_next_page, queue_data=self.__queue_data))
            else:
                # self.send_inform()
                pass
        else:
            pass
            # self.send_inform()
        return {
            'unique_name': 'weibo_blogger_article_list_tag',
            'content': text
        }

import json

import time

from bs4 import BeautifulSoup
from blog_spider.config import *
from blog_spider.model.es.blog_result import BlogResult
from blog_spider.model.task import Task
from blog_spider.page.ins_article import InsArticle
from pyspider.helper.date import Date
from pyspider.helper.utils import generator_list
from pyspider.libs.oss import oss_cdn
from pyspider.libs.webdriver import Webdriver


class InsBlogger:
    """
    抓取 ins 博主信息
    """
    # URL = 'https://www.instagram.com/graphql/query/?query_hash=f2405b236d85e8296cf30347c9f08c2a&variables=' \
    #       '{"id":"6222727723","first":12,"after":""}'
    URL = 'https://www.instagram.com/{}/'

    def __init__(self, account_key, use_proxy=True, priority=0, page=1, to_next_page=False, queue_data=''):
        super(InsBlogger, self).__init__()
        self.__account_key = account_key
        self.__priority = priority
        self.__catch_url = self.URL.format(self.__account_key)
        self.__use_proxy = use_proxy
        self.__page = page
        self.__to_next_page = to_next_page
        self.__queue_data = queue_data
        self.__driver = Webdriver().set_proxy(OUT_PROXY).set_headless().get_driver()

    def entry(self):
        self.__driver.get(self.__catch_url)
        print('开始抓取链接: {}'.format(self.__catch_url))

        # 抓取近15页的数据
        for i in range(BLOGGER_MAX_PAGE):
            # self.__driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            print('i', i)
            # if i == 3:
            break
            time.sleep(2)

        # 保存每个 ins 文章抓取的 page
        page_list = list()
        # 爬虫结果类型
        data_type = 2  # ins
        # 关键词
        # keywords = self.__queue_data.get('keywords', [])
        # 图片是否已经全部都抓完了
        image_crawled = False
        # 是否已经把这条内容发给服务端了
        server_sended = False
        # 内容类型，ins 是 2
        content_type = 2

        print(type(self.__driver.page_source))
        soup = BeautifulSoup(self.__driver.page_source, 'lxml')

        # 用户的唯一标识
        account_key = self.__account_key
        # 用户的用户名
        name = self.__account_key
        # 用户的性别
        sex = ''
        # 单独的每篇文章
        all_data = soup.find_all('div', class_='v1Nh3 kIKUG _bz0w')
        for data in all_data:
            # print('data:{}'.format(data))
            # 标记博主
            is_blogger = True
            # 文章ID
            content_id = data.find('a')['href'].split('/')[-2]
            # 跳过已经抓取过的内容
            if BlogResult().exists(content_id):
                continue
            # continue
            # 用户的头像
            avatar = dict()
            avatar_img = soup.find('span', class_='_2dbep ').find('img')
            avatar_img = avatar_img['src'] if avatar_img else ''
            avatar_img_path = oss_cdn.get_key(oss_cdn.CONST_BLOG_IMAGE + '{}/'.format(content_id),
                                              avatar_img.split('.jpg', 1)[0].split('/')[-1])
            avatar['image'] = avatar_img_path
            avatar['avatar_img'] = avatar_img
            avatar['width'] = 0
            avatar['height'] = 0
            avatar['img_saved'] = False

            content_data = {
                'data_type': data_type,
                'image_crawled': image_crawled,
                'server_sended': server_sended,
                'account_key': account_key,
                'name': name,
                'sex': sex,
                'avatar': avatar,
                'content_id': content_id,
                'is_blogger': is_blogger,
                'content_type': content_type,
            }

            # 解析具体的文章
            page_list.append(InsArticle(content_id, content_data, use_proxy=True))

        self.enqueue_article(page_list)

        print('每个文章模块的个数: {}'.format(len(all_data)))
        # 关闭驱动
        self.__driver.quit()

    def enqueue_article(self, page_list):
        """
        把抓取请求入队
        :param page_list:
        :return:
        """
        limit_list = generator_list(page_list, 10)
        for _m in limit_list:
            # 检测当前抓取的队列数，数量过多则停止写入
            count = Task().find({'status': 1}).count()
            print('queue status:1 count: {}'.format(count))
            while count >= MAX_ALL_QUEUE:
                time.sleep(int(count) / 6)
                count = Task().find({'status': 1}).count()
            for _article in _m:
                print(_article)
                _article.enqueue()
            break

    def _in_task(self, task_id):
        my_task_id = Task().find_one({'taskid': task_id})
        st_id = my_task_id.get('status') if my_task_id else 0
        if st_id == 1:
            # 在队列中
            return True
        else:
            return False

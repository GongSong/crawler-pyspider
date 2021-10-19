from pyspider.core.model.es_base import *


class BlogResult(Base):
    """
    抓取的博客内容，包括帖子内容和博主信息
    """

    def __init__(self):
        super(BlogResult, self).__init__()
        self.cli = es_cli
        self.index = 'blog_result'
        self.test_index = 'blog_result_test'
        self.doc_type = 'data'
        self.primary_keys = 'content_id'

    def get_blog_content(self, search_key, benchmark_time, is_blogger=True, image_crawled=False, server_sended=False,
                         page_size=500, status=1, account_type=1, account_key='', repair=False, images_null=False,
                         images_crawl=False):
        """
        获取图片未抓取完全的内容
        :param search_key: 搜索的类型，博主的是: account_key, 搜索词是: keywords.keyword
        :param is_blogger: 是否是博主内容
        :param benchmark_time: 基准时间：Date.now().plus_hours(-UPDATE_HOUR).timestamp()
        :param image_crawled: 图片是否已经全部被抓取, True: 已抓取, False: 未抓取
        :param server_sended: 是否已经发送了消息通知, True: 已发送, False: 未发送
        :param page_size: 返回的每页数据数量
        :param status: 2：关闭; 1：开启, 0: 不添加status的查询
        :param account_type: 1，weibo；2，ins；
        :param account_key: 指定抓取某个博主的内容
        :param repair: True, 修复过的内容; False, 没有修复过的内容
        :param images_null: 找到images 为空的数据
        :param images_crawl: 检测内容图片是否已经抓取
        :return:
        """
        if is_blogger:
            term_word = 'account_key'
        else:
            term_word = 'keywords.keyword'
        query_builder = EsQueryBuilder() \
            .term('is_blogger', is_blogger) \
            .term('image_crawled', image_crawled) \
            .range_gte('create_time', benchmark_time, None)
        if account_type:
            query_builder.term('data_type', account_type)
        if status:
            query_builder.term('status', status)
        if search_key:
            query_builder.term(term_word, search_key)
        if server_sended:
            query_builder.term('server_sended', server_sended)
        if account_key:
            query_builder.term('account_key', account_key)
        if images_crawl:
            query_builder.match('images.img_saved', False)
        if repair:
            query_builder.term('repair', repair)
        if images_null:
            query_builder.must_not(EsQueryBuilder().exists('images'))
        return self.scroll(query_builder, page_size=page_size)

    def get_all_blogger_msg(self):
        query = EsQueryBuilder() \
            .term('is_blogger', True) \
            .term('status', 1) \
            .aggs(EsAggsBuilder().terms('accout_data', 'account_key', 300)) \
            .search(self, 1, 0) \
            .get_aggregations()['accout_data']['buckets']
        return_list = list()
        for item in query:
            key = item.get('key')
            account = self.get_one_blogger_content(key)
            return_list.append(account)
        return return_list

    def get_one_blogger_content(self, account_key, get_all=False, image_crawled=0):
        """
        获取某个博主的发布内容
        :param account_key: 博主的唯一标识
        :param get_all: 获取博主的所有发布内容
        :param image_crawled: 获取博主的所有发布内容
        :return:
        """
        query_builer = EsQueryBuilder() \
            .term('account_key', account_key) \
            .term('status', 1)
        if image_crawled:
            query_builer.term('image_crawled', True)
        if get_all:
            query = self.scroll(query_builer)
            return query
        else:
            query = query_builer \
                .search(self, 1, 1) \
                .get_one()
            account_dict = dict()
            account_dict['status'] = query['status']
            account_dict['data_type'] = query['data_type']
            account_dict['account_key'] = query['account_key']
            account_dict['keywords'] = query['keywords']
            return account_dict

    def get_all_blog_content_flexible(self, server_sended=0):
        """
        灵活获取所有的博客内容数据；
        字段的筛选可以灵活选择
        :param server_sended: 是否已经发送了消息通知, 0: 不添加该字段的过滤,  1: True: 已发送, 2: False: 未发送
        :return:
        """
        builder = EsQueryBuilder()
        if server_sended:
            if server_sended == 1:
                builder.term('server_sended', True)
            else:
                builder.term('server_sended', False)
        return self.scroll(builder)

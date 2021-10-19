from pyspider.core.model.es_base import *


class BlogMsg(Base):
    """
    博主的信息
    """

    def __init__(self):
        super(BlogMsg, self).__init__()
        self.cli = es_cli
        self.index = 'blog_account_msg'
        self.test_index = 'blog_account_msg_test'
        self.doc_type = 'data'
        self.primary_keys = 'account_key'

    def get_active_content(self, account_type=1, status=1, page_size=50, is_blogger=True, keywords=0):
        """
        获取开启抓取状态的全部博主或者全部关键字
        :param account_type: 1，weibo；2，ins；
        :param status: 2：关闭; 1：开启
        :param page_size: 每次的查询数量
        :param is_blogger: True：博主; False：关键字;
        :param keywords: 0: 不管关键词; 1: 有关键字;
        :return:
        """
        query_builder = EsQueryBuilder() \
            .term('data_type', account_type) \
            .term('status', status)
        if keywords:
            query_builder.exists('keywords')
        return self.scroll(query_builder, page_size=page_size)

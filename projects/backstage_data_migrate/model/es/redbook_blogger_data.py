from pyspider.core.model.es_base import *


class RedbookBloggerData(Base):
    """
    小红书博主的直播数据，带货数据，粉丝分析
    """

    def __init__(self):
        super(RedbookBloggerData, self).__init__()
        self.cli = es_cli
        self.index = 'crawler_redbook_blogger_data'
        self.doc_type = 'data'
        self.primary_keys = 'user_id'

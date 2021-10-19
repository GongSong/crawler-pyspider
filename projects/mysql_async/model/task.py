from pyspider.core.model.mongo_base import *
from pyspider.helper.date import Date


class Task(TaskBase):
    def __init__(self):
        super(Task, self).__init__()

    def clear(self):
        query = {'updatetime': {'$lt': Date.now().plus_hours(1).timestamp()}, 'status': 2}
        delete_count = self.find(query).count()
        if delete_count > 0:
            print('本次删除的task数量:{}, 时间:{}'.format(delete_count, Date.now().format()))
        self.delete_many(query)

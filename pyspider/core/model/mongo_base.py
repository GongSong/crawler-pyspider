from pymongo import MongoClient
from pyspider.config import config
from bson.objectid import ObjectId

from pyspider.libs.utils import get_project_name

mongo_cli = MongoClient(config.get('mongo', 'url'))


class Base(object):
    def __init__(self, database_name='', collection_name=''):
        self.__cli = mongo_cli
        self.__database_name = database_name
        self.__collection_name = collection_name

    @property
    def database(self):
        """get data will check to execute request
        :return:
        """
        return self.__cli.get_database(self.__database_name)

    @property
    def collection(self):
        """get data will check to execute request
        :return:
        """
        return self.database.get_collection(self.__collection_name)

    def find(self, *args, **kwargs):
        """
        see http://api.mongodb.com/python/current/tutorial.html
        :param args:
        :param kwargs:
        :return:
        """
        return self.collection.find(*args, **kwargs)

    def find_one(self, filter=None, *args, **kwargs):
        """
        see http://api.mongodb.com/python/current/tutorial.html
        :param filter:
        :param args:
        :param kwargs:
        :return:
        """
        return self.collection.find_one(filter, *args, **kwargs)

    def insert(self, doc_or_docs, manipulate=True,
               check_keys=True, continue_on_error=False, **kwargs):
        """
        see http://api.mongodb.com/python/current/tutorial.html
        :param doc_or_docs:
        :param manipulate:
        :param check_keys:
        :param continue_on_error:
        :param kwargs:
        :return:
        """
        return self.collection.insert(doc_or_docs, manipulate,
                                      check_keys, continue_on_error, **kwargs)

    def insert_many(self, documents, ordered=True,
                    bypass_document_validation=False, session=None):
        """
        see http://api.mongodb.com/python/current/tutorial.html#bulk-inserts
        :param documents:
        :param ordered:
        :param bypass_document_validation:
        :param session:
        :return:
        """
        return self.collection.insert_many(documents, ordered,
                                           bypass_document_validation, session)

    def update(self, spec, document, upsert=False, manipulate=False,
               multi=False, check_keys=True, **kwargs):
        """
        see http://api.mongodb.com/python/current/tutorial.html
        :param spec:
        :param document:
        :param upsert:
        :param manipulate:
        :param multi:
        :param check_keys:
        :param kwargs:
        :return:
        """
        return self.collection.update(spec, document, upsert, manipulate, multi, check_keys, **kwargs)

    def update_many(self, filter, update, upsert=False, array_filters=None,
                    bypass_document_validation=False, collation=None, session=None):
        """
        see http://api.mongodb.com/python/current/tutorial.html
        :param filter:
        :param update:
        :param upsert:
        :param array_filters:
        :param bypass_document_validation:
        :param collation:
        :param session:
        :return:
        """
        return self.collection.update_many(filter, update, upsert, array_filters,
                                           bypass_document_validation, collation, session)

    def delete_one(self, filter, collation=None, session=None):
        """
        see http://api.mongodb.com/python/current/tutorial.html
        :param filter:
        :param collation:
        :param session:
        :return:
        """
        return self.collection.delete_one(filter, collation, session)

    def delete_many(self, filter, collation=None, session=None):
        """
        see http://api.mongodb.com/python/current/tutorial.html
        :param filter:
        :param collation:
        :param session:
        :return:
        """
        return self.collection.delete_many(filter, collation, session)


class TaskBase(Base):
    def __init__(self):
        super(TaskBase, self).__init__('taskdb', get_project_name(self))


class ResultBase(Base):
    def __init__(self):
        super(ResultBase, self).__init__('resultdb', get_project_name(self))

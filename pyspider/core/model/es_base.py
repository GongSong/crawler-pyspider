from elasticsearch import Elasticsearch
from math import ceil
from pyspider.config import config
from pyspider.helper.logging import logger
from pyspider.helper.es_query_builder import EsQueryBuilder, EsAggsBuilder, EsSearchResultParse
from pyspider.helper.string import merge_str
from pyspider.helper.utils import generator_list

es_cli = Elasticsearch(config.get('es', 'nodes').split(','))


class Base(object):
    def __init__(self):
        self.cli = es_cli
        self.index = ''
        self.doc_type = ''
        self.test_index = ''
        self.primary_keys = ''

    def create_table(self):
        es_map = self.gen_es_map()
        self.cli.transport.perform_request('PUT', '/_template/{}'.format(self.index), body=es_map)
        self.cli.transport.perform_request('PUT', '/{}'.format(self.get_index()))

    def gen_es_map(self):
        template = {
            "template": "{}*".format(self.index),
            "settings": {
                "number_of_shards": 1
            },
            "mappings": {
                "data": {
                    "dynamic_templates": [
                        {
                            "doubles": {
                                "match_mapping_type": "long",
                                "mapping": {
                                    "type": "double"
                                }
                            }
                        },
                        {
                            "strings": {
                                "match_mapping_type": "string",
                                "mapping": {
                                    "type": "keyword"
                                }
                            }
                        },

                    ],
                    "properties": {
                    }
                }
            }
        }
        nest = {
            "type": "nested",
        }
        for _ in self.get_fields_list():
            if _.es_type == "nested":
                template["mappings"]["data"]["properties"][_] = nest
        return template

    def get_index(self):
        if not config.is_product() and self.test_index:
            return self.test_index
        return self.index

    def get_doc_type(self):
        return self.doc_type

    def search(self, query):
        logger.info("esSearch: %s, %s, %s", self.get_index(), self.get_doc_type(), query)
        return self.cli.search(self.get_index(), self.get_doc_type(), query)

    def bulk(self, body, async=False):
        logger.info("esBulk: %s, %s, %s", self.get_index(), self.get_doc_type(), len(body)/2)
        if async:
            from es.page.bulk import Bulk
            Bulk(config.get('es', 'nodes').split(','), self.index, self.doc_type, body).enqueue()
            return
        result = self.cli.bulk(body)
        if result['errors']:
            logger.error("esBulk: %s, %s, %s, %s", self.get_index(), self.get_doc_type(), len(body)/2, result)

    def script_update(self, docs: list, primary_keys=None, async=False):
        if not primary_keys:
            primary_keys = self.primary_keys
        if not primary_keys:
            raise Exception('not found primary keys')
        body = []
        for _ in docs:
            _id = _[primary_keys] if isinstance(primary_keys, str) else merge_str(*(_[_key] for _key in primary_keys), dividing='_')
            body.append({'update': {'_id': _id, '_type': self.get_doc_type(), '_index': self.get_index()}})
            body.append({'script': _.get('script')})
        if len(body) > 0:
            self.bulk(body, async)

    def update(self, docs: list, primary_keys=None, upsert=True, async=False):
        if not primary_keys:
            primary_keys = self.primary_keys
        if not primary_keys:
            raise Exception('not found primary keys')

        for _docs in generator_list(docs, 500):
            body = []
            for _ in _docs:
                _id = _[primary_keys] if isinstance(primary_keys, str) else merge_str(*(_[_key] for _key in primary_keys), dividing='_')
                body.append({'update': {'_id': _id, '_type': self.get_doc_type(), '_index': self.get_index()}})
                body.append({'doc': _, 'doc_as_upsert': upsert})
            if len(body) > 0:
                self.bulk(body, async)

    def delete(self, doc_id):
        self.cli.delete(self.get_index(), self.get_doc_type(), doc_id)

    def batch_delete(self, deleted_ids: list, async=False):
        """
        根据 _id 批量删除数据
        :param deleted_ids:
        :param async:
        :return:
        """
        body = []
        for _id in deleted_ids:
            body.append({"delete": {"_index": self.get_index(), "_type": self.get_doc_type(), "_id": _id}})
        if len(body) > 0:
            self.bulk(body, async)

    def delete_by_query(self, query):
        logger.info("esDeleteByQuery: %s, %s, %s", self.get_index(), self.get_doc_type(), query)
        return self.cli.delete_by_query(self.get_index(), query, self.get_doc_type())

    def exists(self, doc_id):
        return self.cli.exists(self.get_index(), self.get_doc_type(), doc_id)

    def batch_generator(self, query_builder=None, page_size=500, get_id=True):
        """
        批量获取列表
        :param page_size:
        :param query_builder:
        :param get_id:
        :return:
        """
        if query_builder is None:
            query_builder = EsQueryBuilder()
        result = EsSearchResultParse(self.search(query_builder.get_query(1, page_size)))
        count = result.get_count()
        yield result.get_list(get_id)
        page_max = int(ceil(count/page_size))
        for page in range(2, page_max+1):
            yield EsSearchResultParse(self.search(query_builder.get_query(page, page_size))).get_list(get_id)

    def scroll(self, query_builder=None, page_size=500, scroll='5m', print_progress=False, get_id=False):
        """
        scroll
        :param query_builder:
        :param page_size:
        :param scroll:
        :param print_progress:
        :param get_id:
        :return:
        """
        if query_builder is None:
            query_builder = EsQueryBuilder()
        result = EsSearchResultParse(self.cli.search(index=self.get_index(),
                                                     doc_type=self.get_doc_type(),
                                                     body=query_builder.get_query(1, page_size),
                                                     params={'scroll': scroll}))
        scroll_id = result.get_scroll_id()
        count = result.get_count()
        page_max = int(ceil(count/page_size))
        if print_progress:
            print(1, page_max, self.get_doc_type())
        yield result.get_list(get_id)
        for page in range(2, page_max + 1):
            if print_progress:
                print(page, page_max, self.get_doc_type())
            result = EsSearchResultParse(self.cli.scroll(scroll_id=scroll_id, params={'scroll': scroll}))
            scroll_id = result.get_scroll_id()
            yield result.get_list(get_id)
        self.cli.clear_scroll(scroll_id=scroll_id)

    def get_scroll_dict(self, key: str, fields: list, es_builder=EsQueryBuilder()):
        fields.append(key)
        data = {}
        for _scroll in self.scroll(es_builder.source(fields)):
            for _ in _scroll:
                if _.get(key) is None:
                    continue
                data[_[key]] = _
        return data

    def get_scroll_list(self, fields: list, es_builder=EsQueryBuilder()):
        data = []
        for _scroll in self.scroll(es_builder.source(fields)):
            for _ in _scroll:
                data.append(_)
        return data

    @classmethod
    def get_fields_list(cls):
        """
        获取EsField字段字典
        :return:
        """
        return [x for _, x in cls.__dict__.items() if type(x) == EsField]

    def get_last_sync_time(self):
        max_asyc_time = EsQueryBuilder() \
            .aggs(EsAggsBuilder().max('max_sync_time', 'sync_time')) \
            .search(self, 1, 0) \
            .get_aggregations()
        return max_asyc_time['max_sync_time']['value']


class EsField(str):
    er_type = None
    comment = None
    name = None
    parameter = None

    def __new__(cls, value, *args, **kwargs):
        # explicitly only pass value to the str constructor
        return super(EsField, cls).__new__(cls, value)

    def __init__(self, value, es_type='', comment='', name='', parameter=None, *args, **kwargs):
        # ... and don't even call the str initializer
        super().__init__()
        if parameter is None:
            parameter = {}
        self.es_type = es_type
        self.comment = comment
        self.name = name
        self.parameter = parameter
        #是否需要搜索枚举
        self.content = kwargs.get('content')
        #前端显示使用
        self.show_key = kwargs.get('show_key')

        #控制自定义表格是否显示字段
        self.isDataFields = kwargs.get('isDataFields', True)
        self.isDimensionFields = kwargs.get('isDimensionFields', True)
        if es_type == 'date':
            self.isDataFields = False

    def keyword(self):
        return self + '.keyword'

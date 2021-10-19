class EsQueryBuilder:
    """
    elasticsearch query builder
    """

    def __init__(self):
        self.__filters = []
        self.__should = []
        self.__must = []
        self.__must_not = []
        self.__paths = {}
        self.__sort = []
        self.__source = []
        self.__aggs = {}
        self.__minimum_should_match = None

    def search(self, es_model, page=1, page_size=20):
        """
        :param es_model:
        :param page:
        :param page_size:
        :return:
        """
        return EsSearchResultParse(es_model.search(self.get_query(page, page_size)))

    def delete_by_query(self, es_model):
        """
        :param es_model:
        :return:
        """
        return es_model.delete_by_query({'query': self.get_query(1, 0).get('query')})

    def get_query(self, page=1, page_size=20):
        """
        get query
        :param page:
        :param page_size:
        :return:
        """
        return {
            'sort': self.__sort,
            '_source': self.__source,
            'query': {
                'bool': self.get_query_bool_dict()
            },
            'aggs': self.__aggs,
            'from': (page - 1) * page_size,
            'size': page_size
        }

    def get_query_bool_dict(self):
        """
        get bool dict
        :return:
        """
        bool_dict = {}
        if self.get_filters():
            bool_dict.setdefault('filter', self.get_filters())
        if self.__should:
            bool_dict.setdefault('should', self.__should)
            if self.__minimum_should_match:
                bool_dict.setdefault('minimum_should_match', self.__minimum_should_match)
        if self.__must:
            bool_dict.setdefault('must', self.__must)
        if self.__must_not:
            bool_dict.setdefault('must_not', self.__must_not)
        return bool_dict

    def get_filters(self):
        """
        get filters
        :return:
        """
        return self.__filters + self.__get_nested_filters()

    def get_should(self):
        """
        get should
        :return:
        """
        return self.__should

    def get_minimum_should_match(self):
        """
        get minimum should match
        :return:
        """
        return self.__minimum_should_match

    def get_must(self):
        """
        get must
        :return:
        """
        return self.__must

    def get_must_not(self):
        """
        get must not
        :return:
        """
        return self.__must_not

    def script(self, script):
        """
        script
        :param script:
        :return:
        """
        if script is not None:
            self.__append('script', {
                'script': {
                    'script': script
                }
            })

        return self

    def term(self, field, value):
        """
        term
        :param field:
        :param value:
        :return:
        """
        if value is not None:
            self.__append(field, {
                'term': {
                    field: value
                }
            })
        return self

    def terms(self, field, values: list):
        """
        terms
        :param field:
        :param values:
        :return:
        """
        if values is not None and len(values) > 0:
            self.__append(field, {
                'terms': {
                    field: values
                }
            })
        return self

    def range(self, field, start, end):
        """
        range gt lt
        :param field:
        :param start:
        :param end:
        :return:
        """
        if start is not None or end is not None:
            self.__append(field, {
                'range': {
                    field: {
                        'gt': start,
                        'lt': end
                    }
                }
            })
        return self

    def range_e(self, field, start, end):
        """
        range gte lte
        :param field:
        :param start:
        :param end:
        :return:
        """
        if start is not None or end is not None:
            self.__append(field, {
                'range': {
                    field: {
                        'gte': start,
                        'lte': end
                    }
                }
            })
        return self

    def range_gte(self, field, start, end):
        """
        range gte lt
        :param field:
        :param start:
        :param end:
        :return:
        """

        if start is not None or end is not None:
            self.__append(field, {
                'range': {
                    field: {
                        'gte': start,
                        'lt': end
                    }
                }
            })
        return self

    def range_lte(self, field, start, end):
        """
        range gt lte
        :param field:
        :param start:
        :param end:
        :return:
        """
        if start is not None or end is not None:
            self.__append(field, {
                'range': {
                    field: {
                        'gt': start,
                        'lte': end
                    }
                }
            })
        return self

    def exists(self, field):
        """
        exists
        :param field:
        :return:
        """
        self.__append(field, {
            'exists': {
                'field': field
            }
        })
        return self

    def should(self, query_builder):
        """
        should
        :param query_builder:
        :return:
        """
        bool_dict = query_builder.get_query_bool_dict()
        if bool_dict:
            self.__should.append({
                'bool': bool_dict
            })
        return self

    def should_constant_score(self, query_builder, boost=1):
        """
        should
        :param query_builder:
        :param boost:
        :return:
        """
        self.__should.append({
            'constant_score': {
                'filter': query_builder.get_filters().pop(),
                'boost': boost
            }
        })
        return self

    def must(self, query_builder):
        """
        must
        :param query_builder:
        :return:
        """
        bool_dict = query_builder.get_query_bool_dict()
        if bool_dict:
            self.__must.append({
                'bool': bool_dict
            })
        return self

    def must_not(self, query_builder):
        """
        must not
        :param query_builder:
        :return:
        """
        bool_dict = query_builder.get_query_bool_dict()
        if bool_dict:
            self.__must_not.append({
                'bool': bool_dict
            })
        return self

    def minimum_should_match(self, minimum_should_match):
        """
        set minimum_should_match
        :param minimum_should_match:
        :return:
        """
        self.__minimum_should_match = minimum_should_match
        return self

    def match(self, field, value):
        """
        :param field:
        :param value:
        :return:
        """
        if value is not None:
            self.__append('match', {
                'match': {
                    field: value
                }
            })
        return self

    def multi_match(self, fields: list, query: str):
        """
        :param query:
        :param fields:
        :return:
        """
        if query and fields is not None and len(fields) > 0:
            self.__append('multi_match', {
                'multi_match': {
                    'query': query,
                    'fields': fields
                }
            })
        return self

    def regexp(self, field, value):
        """
        regexp
        :param field:
        :param value:
        :return:
        """
        if value is not None:
            self.__append(field, {
                'regexp': {
                    field: value
                }
            })
        return self

    def mysql_fuzzy(self, field, value):
        """
        mysql_like
        :param field:
        :param value:
        :return:
        """
        if value:
            self.regexp(field, '.*%s.*' % value)
        return self

    def add_sort(self, field, sort_type='desc'):
        """
        add sort
        :param field:
        :param sort_type:
        :return:
        """
        self.__sort.append({
            field: sort_type
        })
        return self

    def source(self, fields: list):
        """
        es result source
        :param fields:
        :return:
        """
        self.__source = fields
        return self

    def aggs(self, aggs):
        """
        aggs
        :param aggs:
        :return:
        """
        self.__aggs = aggs.get_aggs() if isinstance(aggs, EsAggsBuilder) else aggs
        return self

    def __get_nested_filters(self):
        """
        nested filters
        :return:
        """
        result = []
        for path, filters in self.__paths.items():
            result.append({
                'nested': {
                    'path': path,
                    'query': {
                        'bool': {
                            'filter': filters
                        }
                    }
                }
            })
        return result

    def __append(self, field, f):
        """
        append filter
        :param field:
        :param f:
        :return:
        """
        if '.' in field.replace('.keyword', ''):
            path = field.split('.')[0]
            self.__paths.setdefault(path, [])
            self.__paths[path].append(f)
        else:
            self.__filters.append(f)


class EsAggsBuilder:
    """
    elasticsearch aggs builder
    """

    def __init__(self):
        self.__names = {}
        self.__last_name = None

    def get_aggs(self):
        """
        get aggs
        :return:
        """
        return self.__names

    def terms_script(self, name, script, size=1000):
        """
        terms script aggs
        :param name:
        :param script:
        :param size:
        :return:
        """
        self.__names[name] = {
            'terms': {
                'size': size,
                'script': {
                    'lang': 'painless',
                    'inline': script
                }
            }
        }
        self.__last_name = name
        return self

    def terms(self, name, field, size=1000, min_doc_count=0):
        """
        terms agg
        :param name:
        :param field:
        :param size:
        :param min_doc_count:
        :return:
        """
        aggs_terms = {
            'terms': {
                'field': field,
                'size': size
            }
        }
        if min_doc_count:
            aggs_terms['terms']['min_doc_count'] = min_doc_count
        self.__names[name] = aggs_terms
        self.__last_name = name
        return self

    def terms_nested(self, name, field, size=1000):
        """
        nested terms
        :param name:
        :param field:
        :param size:
        :return:
        """
        path = field.split('.')[0]
        self.__names[name] = {
            "nested": {
                "path": path
            },
            "aggs": {
                name: {
                    "terms": {
                        "field": field,
                        "size": size
                    }
                }
            }
        }
        self.__last_name = name
        return self

    def cardinality_script(self, name, script):
        """
        cardinality script agg
        :param name:
        :param script:
        :return:
        """
        self.__names[name] = {
            'cardinality': {
                'script': {
                    'lang': 'painless',
                    'inline': script
                }
            }
        }
        return self

    def cardinality(self, name, field):
        """
        cardinality agg
        :param name:
        :param field:
        :return:
        """
        self.__names[name] = {
            'cardinality': {
                'field': field
            }
        }
        return self

    def percentiles(self, name, field):
        """
        percentiles agg
        :param name:
        :param field:
        :return:
        """
        self.__names[name] = {
            'percentiles': {
                'field': field
            }
        }
        return self

    def sum(self, name, field):
        """
        sum agg
        :param name:
        :param field:
        :return:
        """
        self.__names[name] = {
            'sum': {
                'field': field
            }
        }
        return self

    def sum_script(self, name, script):
        """
        sum agg
        :param name:
        :param script:
        :return:
        """
        self.__names[name] = {
            'sum': {
                'script': {
                    'lang': 'painless',
                    'inline': script
                }
            }
        }
        return self

    def min(self, name, field):
        """
        min agg
        :param name:
        :param field:
        :return:
        """
        self.__names[name] = {
            'min': {
                'field': field
            }
        }
        return self

    def max(self, name, field):
        """
        max agg
        :param name:
        :param field:
        :return:
        """
        self.__names[name] = {
            'max': {
                'field': field
            }
        }
        return self

    def avg(self, name, field):
        """
        avg agg
        :param name:
        :param field:
        :return:
        """
        self.__names[name] = {
            'avg': {
                'field': field
            }
        }
        return self

    def top_hits(self, name, size=1, sort_field=None, sort_type='desc'):
        """
        top hits
        :param name:
        :param size:
        :param sort_field:
        :param sort_type:
        :return:
        """
        self.__names[name] = {
            'top_hits': {
                'size': size,
            }
        }
        if sort_field:
            self.__names[name]['top_hits']['sort'] = {
                sort_field: sort_type
            }
        return self

    def date_histogram(self, name, field, interval, time_zone=None, order=None, extended_bounds=None, min_doc_count=None):
        """
        date histogram
        :param min_doc_count:
        :param extended_bounds:
        :param name:
        :param field:
        :param interval:
        :param time_zone:
        :param order:
        :return:
        """
        self.__names[name] = {
            'date_histogram': {k: v for k, v in {
                'field': field,
                'interval': interval,
                'time_zone': time_zone,
                'order': order,
                'min_doc_count': min_doc_count,
                'extended_bounds': {
                    'min': extended_bounds[0],
                    "max": extended_bounds[1]
                } if extended_bounds else extended_bounds,
            }.items() if v is not None}
        }
        self.__last_name = name
        return self

    def nested(self, name, field):
        """
        nested path
        :param name:
        :param field:
        :return:
        """
        self.__names[name] = {
            'nested': {
                'path': field
            }
        }
        self.__last_name = name
        return self

    def reverse_nested(self, name):
        self.__names[name] = {
            'reverse_nested': {}
        }
        self.__last_name = name
        return self

    def aggs(self, aggs):
        """
        nested aggs
        :param aggs:
        :return:
        """
        if aggs and isinstance(aggs, EsAggsBuilder) and self.__last_name in self.__names:
            self.__names[self.__last_name]['aggs'] = aggs.get_aggs()
        return self

    def filter_query(self, name, query: EsQueryBuilder):
        """
        filter term
        :param name:
        :param query:
        :return:
        """
        self.__names[name] = {
            'filter': {
                'bool': query.get_query_bool_dict()
            }
        }
        self.__last_name = name
        return self

    def filter_term(self, name, field, value):
        """
        filter term
        :param name:
        :param field:
        :param value:
        :return:
        """
        self.__names[name] = {
            'filter': {
                'term': {
                    field: value
                }
            }
        }
        self.__last_name = name
        return self

    def filter_terms(self, name, field, values: list):
        """
        filter terms
        :param name:
        :param field:
        :param values:
        :return:
        """
        self.__names[name] = {
            'filter': {
                'terms': {
                    field: values
                }
            }
        }
        self.__last_name = name
        return self

    def filter_range(self, name, field, start, end):
        """
        filter range gt lt
        :param name:
        :param field:
        :param start:
        :param end:
        :return:
        """
        self.__names[name] = {
            'filter': {
                'range': {
                    field: {
                        'gt': start,
                        'lt': end
                    }
                }
            }
        }
        self.__last_name = name
        return self

    def filter_range_e(self, name, field, start, end):
        """
        filter range gte lte
        :param name:
        :param field:
        :param start:
        :param end:
        :return:
        """
        self.__names[name] = {
            'filter': {
                'range': {
                    field: {
                        'gte': start,
                        'lte': end
                    }
                }
            }
        }
        self.__last_name = name
        return self

    def filter_range_gte(self, name, field, start, end):
        """
        filter range gte lt
        :param name: str
        :param field:
        :param start:
        :param end:
        :return:
        """
        self.__names[name] = {
            'filter': {
                'range': {
                    field: {
                        'gte': start,
                        'lt': end
                    }
                }
            }
        }
        self.__last_name = name
        return self

    def filter_range_lte(self, name, field, start, end):
        """
        filter range gt lte
        :param name:
        :param field:
        :param start:
        :param end:
        :return:
        """
        self.__names[name] = {
            'filter': {
                'range': {
                    field: {
                        'gt': start,
                        'lte': end
                    }
                }
            }
        }
        self.__last_name = name
        return self

    def stats(self, name, field):
        """
        stats agg
        :param name:
        :param field:
        :return:
        """
        self.__names[name] = {
            'stats': {
                'field': field
            }
        }
        return self


class EsSearchResultParse:
    """
    elasticsearch search result parse
    """

    def __init__(self, result):
        self.result = result

    def get_list(self, get_id=True):
        """
        get list
        :return:
        """
        return_data = []
        for _ in self.result['hits']['hits']:
            if get_id:
                _['_source']['_id'] = _['_id']
            return_data.append(_['_source'])
        return return_data

    def get_one(self):
        """
        get one
        :return:
        """
        result = self.get_list()
        return self.get_list()[0] if result else {}

    def get_count(self):
        """
        get count
        :return:
        """
        return self.result['hits']['total']

    def get_aggregations(self):
        """
        get aggregations
        :return:
        """
        return self.result['aggregations']

    def get_scroll_id(self):
        """
        get scroll id
        :return:
        """
        return self.result['_scroll_id']

    def get_list_and_count(self, get_id=True):
        """
        get list and count
        :param get_id:
        :return:
        """
        return self.get_list(get_id), self.get_count()

    def __iter__(self):
        for _ in self.get_list():
            yield _

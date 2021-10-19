from .http_base import *


class HttpSimple(HttpBase):
    def __init__(self):
        super(HttpSimple, self).__init__()
        self.__headers = {}
        self.__url = ''
        self.__params = {}
        self.__method = HttpMethod.GET
        self.__is_request_json = False

    def set_method(self, method):
        self.__method = method
        return self

    def get_method(self):
        return self.__method

    def set_url(self, url):
        self.__url = url
        return self

    def get_url(self):
        return self.__url

    def set_params(self, params):
        self.__params = params
        return self

    def set_param(self, key, value):
        self.__params[key] = value
        return self

    def get_params(self):
        return self.__params

    def set_is_request_json(self, is_request_json):
        self.__is_request_json = is_request_json
        self.set_method(HttpMethod.POST)
        return self

    def set_header(self, key, value):
        self.__headers[key] = value
        return self

    def set_headers(self, headers):
        self.__headers = headers
        return self

    def set_page(self, page):
        self.set_param('page', page)
        return self

    def set_page_size(self, page_size):
        self.set_param('pageSize', page_size)
        return self

    def build_grequest(self):
        logger.debug('http simple URL: %s, PARAMS: %s, HEADERS: %s', self.__url, self.__params, self.__headers)
        if self.__method == HttpMethod.POST:
            if self.__is_request_json:
                self.set_header('content-type', 'application/json')
                return grequests.post(self.__url, data=json.dumps(self.__params), headers=self.__headers)
            return grequests.post(self.__url, data=self.__params, headers=self.__headers)
        else:
            return grequests.get(self.__url, params=self.__params, headers=self.__headers)

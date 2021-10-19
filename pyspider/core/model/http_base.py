import requests
import grequests
import json
from abc import ABC, abstractmethod
from enum import Enum, auto
from pyspider.helper.logging import logger


class DataType:
    TEXT = auto()
    JSON = auto()
    BYTES = auto()


class HttpMethod:
    POST = auto()
    GET = auto()


class HttpBase(ABC):
    # TODO to optimize the container
    http_container = []

    def __init__(self):
        self.__executed = False
        self.__data_type = DataType.JSON
        self.__data = None
        self.__response = None
        self.__encoding = 'utf8'
        HttpBase.http_container.append(self)

    def reload(self):
        """
        reload response
        :return:
        """
        if self.__executed:
            self.__executed = False
            HttpBase.http_container.append(self)
        return self

    @property
    def data(self):
        """get data will check to execute request
        :return:
        """
        if not self.__executed:
            HttpBase.execute()
        return self.__data

    def set_data(self, data):
        """
        cover response data
        :param data:
        :return:
        """
        self.__data = data
        return self


    @property
    def data_type(self):
        """
        :return:
        """
        return self.__data_type

    @data_type.setter
    def data_type(self, value):
        """
        :return:
        """
        self.__data_type = value

    def set_data_type(self, data_type):
        """
        :param data_type:
        :return:
        """
        self.data_type = data_type
        return self

    @property
    def encoding(self):
        """
        :return:
        """
        return self.__encoding

    @encoding.setter
    def encoding(self, value):
        """
        :return:
        """
        self.__encoding = value

    def set_encoding(self, encoding):
        """set encoding. default: utf8
        :param encoding:
        :return:
        """
        self.__encoding = encoding
        return self

    @property
    def response(self):
        """
        :return:
        :rtype: requests.Response
        """
        return self.__response

    @response.setter
    def response(self, value):
        """set response and format data
        :param value:
        :return:
        """
        self.__response = value
        self.__executed = True
        if self.response is None:
            logger.error('response is none')
            return
        self.response.encoding = self.__encoding
        logger.info(self.response.text)
        if self.__data_type == DataType.JSON:
            self.__data = self.response.json()
        elif self.__data_type == DataType.TEXT:
            self.__data = self.response.text
        else:
            self.__data = self.response.content

    @staticmethod
    def execute():
        """execute all requests and set response to model object
        :return:
        """
        if not HttpBase.http_container:
            return
        for _object, _resp in zip(HttpBase.http_container, grequests.map(
                [_.build_grequest() for _ in HttpBase.http_container],
                exception_handler=lambda r, e: logger.error('request_err: %s, %s', r, e)
        )):
            _object.response = _resp
        HttpBase.http_container = []

    @abstractmethod
    def build_grequest(self):
        pass



import uuid

from bs4 import BeautifulSoup

from backstage_data_migrate.model.es.SycmAiWords import SycmAiWords
from pyspider.helper.string import merge_str
from pyspider.libs.base_crawl import *
from pyspider.helper.date import Date
from pyspider.helper.logging import processor_logger
from backstage_data_migrate.config import *


class SycmAiTagWords(BaseCrawl):
    """
    获取生意参谋 后台的搜索词数据
    """
    URL = 'https://www.baidu.com/'

    def __init__(self, data, date_str, category, key_type):
        super(SycmAiTagWords, self).__init__()
        self.__url = self.URL
        self.__date = date_str
        self.__category = category
        self.__key_type = key_type
        self.__data = data

    def crawl_builder(self):
        return CrawlBuilder() \
            .set_url(self.__url) \
            .set_headers_kv('User-Agent', USER_AGENT) \
            .set_task_id(md5string(self.__url + str(uuid.uuid4())))

    def parse_response(self, response, task):
        processor_logger.info('date: {}'.format(self.__date))
        processor_logger.info('category: {}'.format(self.__category))
        processor_logger.info('key_type: {}'.format(self.__key_type))
        sync_time = Date.now().format_es_utc_with_tz()
        soup = BeautifulSoup(self.__data, 'lxml')
        tr_items = soup.find_all('tr', class_='ant-table-row')
        save_list = []
        for tr in tr_items:
            td_items = tr.find_all('td')
            if self.__key_type == '搜索词':
                # 搜索词
                key = ''.join([i.get_text() for i in td_items[0].find_all('span')])
                # 热搜排名
                searchRank = ''.join([i.get_text() for i in td_items[1].find_all('span')])
                searchRank = int(searchRank)
                # 搜索人气
                search = ''.join([i.get_text() for i in td_items[2].find_all('span')])
                search = int(search.replace(',', '').replace('-', '0'))
                # 点击人气
                click = ''.join([i.get_text() for i in td_items[3].find_all('span')])
                click = int(click.replace(',', '').replace('-', '0'))
                # 点击率
                clickRate = ''.join([i.get_text() for i in td_items[4].find_all('span')])
                clickRate = float(clickRate.replace('%', '').replace(',', '').replace('-', '0')) / 100
                # 支付转化率
                payRate = ''.join([i.get_text() for i in td_items[5].find_all('span')])
                payRate = float(payRate.replace('%', '').replace(',', '').replace('-', '0')) / 100

                save_dict = {
                    'category': self.__category,
                    'date': self.__date,
                    'keyType': self.__key_type,
                    'key': key,
                    'searchRank': searchRank,
                    'search': search,
                    'click': click,
                    'clickRate': clickRate,
                    'payRate': payRate,
                    'sync_time': sync_time,
                }
                save_list.append(save_dict)
                self.send_message(save_dict,
                                  merge_str('sycm_words', self.__category, self.__date, self.__key_type, key))
            else:
                # 搜索词
                key = ''.join([i.get_text() for i in td_items[0].find_all('span')])
                # 热搜排名
                hotRank = ''.join([i.get_text() for i in td_items[1].find_all('span')])
                hotRank = int(hotRank)
                # 相关搜索词数
                about = ''.join([i.get_text() for i in td_items[2].find_all('span')])
                about = int(about.replace(',', '').replace('-', '0'))
                # 相关词搜索人气
                aboutSearch = ''.join([i.get_text() for i in td_items[3].find_all('span')])
                aboutSearch = int(aboutSearch.replace(',', '').replace('-', '0'))
                # 相关词点击人气
                aboutClick = ''.join([i.get_text() for i in td_items[4].find_all('span')])
                aboutClick = int(aboutClick.replace(',', '').replace('-', '0'))
                # 词均点击率
                wordClickRate = ''.join([i.get_text() for i in td_items[5].find_all('span')])
                wordClickRate = float(wordClickRate.replace('%', '').replace(',', '').replace('-', '0')) / 100
                # 词均支付转化率
                wordPayRate = ''.join([i.get_text() for i in td_items[6].find_all('span')])
                wordPayRate = float(wordPayRate.replace('%', '').replace(',', '').replace('-', '0')) / 100

                save_dict = {
                    'category': self.__category,
                    'date': self.__date,
                    'keyType': self.__key_type,
                    'key': key,
                    'hotRank': hotRank,
                    'about': about,
                    'aboutSearch': aboutSearch,
                    'aboutClick': aboutClick,
                    'wordClickRate': wordClickRate,
                    'wordPayRate': wordPayRate,
                    'sync_time': sync_time,
                }
                save_list.append(save_dict)

        SycmAiWords().update(save_list, async=True)
        return {
            'save_dict': save_list,
            'unique_name': 'sycm_words',
            'sync_time': sync_time,
        }

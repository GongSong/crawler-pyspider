from peewee import *
from pyspider.helper.logging import logger
from pyspider.config import config

db = MySQLDatabase(config.get('mysql', 'database'),
                   user=config.get('mysql', 'user'),
                   charset='utf8',
                   password=config.get('mysql', 'password'),
                   host=config.get('mysql', 'host'),
                   port=int(config.get('mysql', 'port')))

erp_db = MySQLDatabase(config.get('erp_mysql', 'database'),
                   user=config.get('erp_mysql', 'user'),
                   charset='utf8',
                   password=config.get('erp_mysql', 'password'),
                   host=config.get('erp_mysql', 'host'),
                   port=int(config.get('erp_mysql', 'port')))

erp_shop_db = MySQLDatabase(config.get('erp_shop_mysql', 'database'),
                   user=config.get('erp_shop_mysql', 'user'),
                   charset='utf8',
                   password=config.get('erp_shop_mysql', 'password'),
                   host=config.get('erp_shop_mysql', 'host'),
                   port=int(config.get('erp_shop_mysql', 'port')))

xs_report_db = MySQLDatabase(config.get('xs_report_mysql', 'database'),
                            user=config.get('xs_report_mysql', 'user'),
                            charset='utf8',
                            password=config.get('xs_report_mysql', 'password'),
                            host=config.get('xs_report_mysql', 'host'),
                            port=int(config.get('xs_report_mysql', 'port')))

retail_order_db = MySQLDatabase(config.get('retail_order_mysql', 'database'),
                             user=config.get('retail_order_mysql', 'user'),
                             charset='utf8',
                             password=config.get('retail_order_mysql', 'password'),
                             host=config.get('retail_order_mysql', 'host'),
                             port=int(config.get('retail_order_mysql', 'port')))

tg_common_db = MySQLDatabase(config.get('tg_common_mysql', 'database'),
                                user=config.get('retail_order_mysql', 'user'),
                                charset='utf8',
                                password=config.get('retail_order_mysql', 'password'),
                                host=config.get('retail_order_mysql', 'host'),
                                port=int(config.get('retail_order_mysql', 'port')))
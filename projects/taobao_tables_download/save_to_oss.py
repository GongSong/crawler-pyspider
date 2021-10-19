from alarm.page.ding_talk import DingTalk
from pyspider.libs.base_crawl import *
from taobao_tables_download.config import *


def save_to_oss(file_name, response, channel):
    split_name_list = file_name.split('T', 1)
    if len(response.content) < 3000:
        return False
    else:
        file_path = oss.get_key(
            oss.CONST_SYCM_SHOP_PATH, '{}/{}/{}.xls'.format(channel, split_name_list[0], split_name_list[1])
        )
        oss.upload_data(file_path, response.content)
        return True

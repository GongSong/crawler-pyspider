import mitmproxy
from mitmproxy import ctx
from mitmproxy.http import HTTPFlow

from pyspider.config import config
from pyspider.helper.date import Date
from aiimage.model.result import Result
from pyspider.helper.logging import mitmproxy_logger
from pyspider.helper.string import json_loads
from pyspider.libs.response import get_encoding
from pyspider.libs.utils import md5string
from PIL import Image
import os


class Hook:
    def response(self, flow: HTTPFlow):
        url = flow.request.pretty_url
        taskid = md5string(url)
        image_suffix, last_modified, content_type = self.__detect_headers(flow.response.headers)
        host = flow.request.host

        data = {
            'taskid': taskid,
            'content_type': content_type,
            'last_modified': last_modified,
            'rep_headers': flow.response.headers,
            'req_headers': flow.request.headers,
            'url': url,
            'host': host,
            'updatetime': Date.now().timestamp(),
        }
        if flow.response.content:
            data['content_len'] = len(flow.response.content)

        # 保存图片
        if image_suffix:
            data.update(self.__save_image(flow.response.content, host, taskid, image_suffix, last_modified, url))
        else:
            try:
                encoding = get_encoding(flow.response.headers, flow.response.content)
                if encoding and encoding.lower() == 'gb2312':
                    encoding = 'gb18030'
                result = flow.response.content.decode(encoding if encoding else 'utf-8', 'replace')
                if 'json' in content_type:
                    result = json_loads(result)
            except Exception as e:
                result = str(e)
            data['result'] = result if len(result) <= 102400 or host == 'mp.weixin.qq.com' else 'TOOLONG'
        Result().update({'taskid': taskid}, {"$set": data}, upsert=True)

    @staticmethod
    def __detect_headers(headers):
        image_suffix = ''
        last_modified = ''
        content_type = ''
        try:
            for _key, _value in headers.items():
                _key_name = _key.lower()
                if _key_name == 'content-type':
                    content_type = _value
                    if _value.startswith('image/') and ';' not in _value:
                        image_suffix = '.'+_value.split('/')[1]
                elif _key_name == 'last-modified':
                    last_modified = Date(_value).format()
        except Exception as e:
            mitmproxy_logger.warn({'type': 'modify time err', 'err': e})
        return image_suffix, last_modified, content_type

    @staticmethod
    def __get_image_path(host, taskid, image_suffix, last_modified):
        image_dir = '{}/image/{}/{}'.format(config.get('log', 'log_dir'), host,
                                            Date(last_modified).format(full=False) if last_modified else 'unknown')
        image_full_path = '{}/{}{}'.format(image_dir, taskid, image_suffix)
        return image_dir, image_full_path

    @staticmethod
    def __save_image(content, host, taskid, image_suffix, last_modified, url):
        data = {}
        image_dir, image_path = Hook.__get_image_path(host, taskid, image_suffix, last_modified)
        if not content:
            mitmproxy_logger.warn({'image_path': image_path, 'url': url})
        else:
            if not os.path.isdir(image_dir):
                os.makedirs(image_dir)
            with open(image_path, 'wb') as f:
                f.write(content)
            # image_width, image_height = Image.open(image_path).size
            data = {
                'image_path': image_path,
                # 'image_width': image_width,
                # 'image_height': image_height,
            }
        return data


addons = [
    Hook()
]

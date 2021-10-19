from PIL import Image
import re
import fire
from pyquery import PyQuery
from aiimage.model.es.fashion_words import FashionWords
from pyspider.config import config
from pyspider.helper.date import Date
from aiimage.model.result import Result
from aiimage.model.es.fashion_images import FashionImages
from pyspider.helper.es_query_builder import EsQueryBuilder
from pyspider.helper.utils import division
from pyspider.libs.oss import Oss
from pyspider.libs.utils import md5string
import jieba
import jieba.analyse
from collections import Counter
# 添加自定义词库
jieba.add_word('白富美')

host_assoc = {
    'assets.burberry.com': 'Burberry',
    'cdn3.yoox.biz': 'chloe',
    'www.chloe.cn': 'chloe',
    'www.chanel.com': 'CHANEL',
    'www.fendi.cn': 'FENDI',
    'a.vpimg2.com': 'FENDI',
    'www.louisvuitton.cn': 'LV',
    'www.prada.com': 'PRADA',
    'wwws.dior.com': 'DIOR',
    'www.dior.com': 'DIOR',
    'assets.hermes.cn': 'Hermès',
    'res.gucci.cn': 'gucci',
    'www.celine.com': 'celine',
    'www.tods.com': 'tods',
    'china.coach.com': 'coach',
    'img.china.coach.com': 'coach',
    'd2ls16jjuwnppu.cloudfront.net': 'Dolce & Gabbana',
    'www.givenchy.com': 'Givenchy',
    'www.jacquemus.com': 'Jacquemus',
    'www.loewe.com': 'loewe',
    'www.stellamccartney.com': 'Stella MaCartney',
    'www.thombrowne.cn': 'Thom Browne',
    'www.versace.cn': 'Versace',
    'www.ysl.com': 'ysl',
    'assets.miumiu.com': 'miumiu',
    'valentino-cdn.thron.com': 'Valentino',
}


class Cron:
    def __init__(self):
        self.__oss_cdn = self.__get_oss_cdn()
        self.__batch_docs = []

    def sync_brand_to_ai(self, seconds=300, force_update_es=False):
        """
        同步品牌图片到ai后台的es
        :param seconds:
        :param force_update_es:
        :return:
        """
        find_dict = {
            'updatetime': {'$gt': Date.now().plus_seconds(-seconds).timestamp()},
            'content_len': {'$gt': 20480},
            'last_modified': {'$ne': ''},
            'image_path': {'$exists': True}
        }
        if not force_update_es:
            find_dict['sync_time'] = None

        for _ in Result().find(find_dict):
            if 'xml' in _['content_type']:
                continue
            brand_name = host_assoc.get(_['host'])
            if brand_name:
                self.__sync_image_to_ai(_, 'brand', brand_name, _['last_modified'])
        self.__batch_update_to_es()

    def sync_star_to_ai(self, seconds=300, force_update_es=False):
        """
        同比明星图片到ai后台的es
        :param seconds:
        :param force_update_es:
        :return:
        """
        find_dict = {
            'updatetime': {'$gt': Date.now().plus_seconds(-seconds).timestamp()},
            'host': {'$in': ['www.deepfashion.cn', 'zhiyi-image-cdn.zhiyitech.cn', 'zhiyi-image.oss-cn-hangzhou.aliyuncs.com']}
        }
        if not force_update_es:
            find_dict['sync_time'] = None

        image_dict = {}
        for _ in Result().find(find_dict):
            if _['url'].startswith('https://www.deepfashion.cn/blog/query/follow'):
                try:
                    result = _['result'].get('result', {}).get('resultList', [])
                    for _media in result:
                        image_dict.setdefault(_media['mediaUrl'].split('?')[0], {}).update(
                            {
                                'nickname': _media['blogger']['nickname'],
                                'fullName': _media['blogger']['fullName'],
                                'mainTaskid': _['taskid'],
                                'postTime': _media['postTime'],
                            })
                except Exception as e:
                    print(e)
                    pass
            elif _.get('image_path'):
                image_dict.setdefault(_['url'].split('?')[0], {}).update(
                    {
                        'taskid': _['taskid'],
                        'image_path': _['image_path'],
                        'oss_key': _.get('oss_key'),
                        'image_width': _.get('image_width'),
                        'image_height': _.get('image_height'),
                        'url': _.get('url')
                    })
        for _ in image_dict.values():
            if _.get('taskid') and _.get('fullName'):
                self.__sync_image_to_ai(_, 'star', _['fullName'], _['postTime'])
        self.__batch_update_to_es()

    def remove_duplicate(self, days=30):
        """
        图片排重
        :return:
        """
        urls = {}
        for _list in FashionImages().scroll(
                EsQueryBuilder()
                        .range('time', Date.now().plus_days(-days).format_es_utc_with_tz(), None)
                        .must_not(EsQueryBuilder().term('show', 0))
                        .source(['originalUrl', 'imageId', 'width'])
        ):
            for _ in _list:
                if _.get('originalUrl'):
                    # https://www.prada.com/content/dam/prada/2019/002_collections/SS19_resort/Women/looks/16.jpg/_jcr_content/renditions/cq5dam.web.580.580.jpg
                    # https://www.prada.com/content/dam/prada/2019/002_collections/SS19_resort/Women/looks/16.jpg/_jcr_content/renditions/cq5dam.web.1280.1280.jpg
                    # https://res.gucci.cn/resources/2019/3/21/15531342186466224_ws_316X316.jpg
                    # https://res.gucci.cn/resources/2019/3/21/15531342186466224_ts_470X470.png
                    # https://res.gucci.cn/resources/2019/3/12/15523665801673911_content_DarkGray_CategoryDoubleVertical_Standard_463x926_1550141105_CategoryDoubleVertical_S91-FS-MNWLook070_001_Light.jpg
                    # https://res.gucci.cn/resources/2019/3/12/15523665801677798_content_LightGray_CategoryDoubleVertical_Standard_463x926_1550141105_CategoryDoubleVertical_S91-FS-MNWLook070_001_Light.jpg
                    url = _['originalUrl'].split('?')[0]
                    # 有些url会多一个//
                    url = url.replace('//', '/')
                    find = re.findall(r'.*res.gucci.cn.*\d+x\d+_(\d+)_', url)
                    if find:
                        url = find[0]
                    else:
                        url = re.sub(r'(_ts_|_ws_)?[0-9]+[X\.][0-9]+\.(jpg|png)$', '', url)
                    urls.setdefault(url, []).append(_)
        for _list in urls.values():
            if len(_list) > 1:
                image_ids = []
                max_width_image_id = None
                max_width = 0
                for _ in _list:
                    image_ids.append(_['imageId'])
                    if _['width'] > max_width:
                        max_width_image_id = _['imageId']
                        max_width = _['width']
                for _image_id in image_ids:
                    if _image_id != max_width_image_id:
                        print(_image_id)
                        FashionImages().update([{
                            'imageId': _image_id,
                            'maxWidthImageId': max_width_image_id,
                            'show': 0,
                        }])

    def __get_oss_cdn(self):
        return Oss(config.get('oss_cdn', 'access_key_id'),
                   config.get('oss_cdn', 'access_key_secret'),
                   config.get('oss_cdn', 'bucket_name'),
                   config.get('oss_cdn', 'endpoint'))

    def __sync_image_to_ai(self, task, type_name, name, time):
        """
        同比图片到ai后台的es
        :param taskid:
        :param image_path:
        :param type_name:
        :param name:
        :param time:
        :return:
        """
        taskid = task.get('taskid')
        image_path = task.get('image_path')
        oss_key = task.get('oss_key')
        image_width = task.get('image_width')
        image_height = task.get('image_height')
        url = task.get('url')
        if not oss_key:
            path_arr = image_path.split('.')
            image_type = path_arr[len(path_arr)-1]
            image = Image.open(image_path)
            image_width, image_height = image.size
            if image_type == 'webp':
                path_arr[len(path_arr)-1] = 'jpeg'
                image_path = '.'.join(path_arr)
                if image.mode in ('RGBA', 'LA'):
                    image = image.convert('RGB')
                image.save(image_path)
                image_type = 'jpeg'
            oss_key = self.__oss_cdn.get_key(self.__oss_cdn.CONST_AI_IMAGE, taskid+'.'+image_type)
            if not self.__oss_cdn.is_had(oss_key):
                self.__oss_cdn.upload_from_file(oss_key, image_path)
            Result().update({'taskid': taskid}, {"$set": {
                'taskid': taskid,
                'sync_time': Date.now().format(),
                'image_width': image_width,
                'image_height': image_height,
                'aspect_ratio': division(image_height, image_width, 1),
                'oss_key': oss_key,
            }}, upsert=True)
        self.__batch_docs.append({
            'imageId': taskid,
            'type': type_name,
            'image': config.get('oss_cdn', 'cdn_domain')+oss_key,
            'width': image_width,
            'height': image_height,
            'name': name,
            'tags': [],
            'time': Date(time).format_es_utc_with_tz(),
            'aspectRatio': division(image_height, image_width, 1),
            'originalUrl': url
        })
        self.__batch_update_to_es(False)

    def __batch_update_to_es(self, force=True):
        if len(self.__batch_docs) < 100 and not force:
            return
        print(len(self.__batch_docs))
        if self.__batch_docs:
            FashionImages().update(self.__batch_docs)
            self.__batch_docs = []

    def wechat(self, seconds=300):
        """
        微信公众号内容词频分析
        :param seconds:
        :return:
        """
        find_dict = {
            'updatetime': {'$gt': Date.now().plus_seconds(-seconds).timestamp()},
            'host': 'mp.weixin.qq.com',
            'image_path': {'$exists': False},
        }
        contents = {}
        for _ in Result().find(find_dict):
            if not _['url'].startswith('https://mp.weixin.qq.com/s?'):
                continue
            pq = PyQuery(_['result'])
            title = pq.find('#activity-name').text().strip()
            username = pq.find('#js_name').text().strip()
            content_id = md5string(username+':'+title)
            if content_id in contents:
                continue
            create_date = 0
            publish_time = 0
            find = re.findall(r'var createDate=new Date\("(\d+)"\*1000\)', _['result'])
            if find:
                create_date = find[0]
            find = re.findall(r'var publish_time = \"(\d+-\d+-\d+)"', _['result'])
            if find:
                publish_time = find[0]
            text = pq.find('#js_content').text()
            words = self.__get_words1(text)
            nested_words = []
            for _word in words:
                nested_words.append({'name': _word})
            contents.setdefault(content_id, {'contentId': content_id,
                                             'nestedWords': nested_words,
                                             'title': title,
                                             'createTime': Date(create_date).format_es_utc_with_tz(),
                                             'publishTime': Date(publish_time).format_es_utc_with_tz(),
                                             'username': username})
        FashionWords().update(contents.values())

    def __get_words1(self, text):
        """
        直接获取结巴分词结果
        :param text:
        :return:
        """
        stopwords = []
        with open('aiimage/ChineseStopWords.txt') as f:
            for _ in f:
                stopwords.append(_.strip())
        words = jieba.cut(text)
        result = []
        for _word in words:
            if _word in stopwords:
                continue
            if len(_word) > 1 and _word != '\r\n':
                result.append(_word)
        return result

    def __get_words2(self, text):
        """
        输出结巴分词结果，并返回top100
        :param text:
        :return:
        """
        stopwords = []
        with open('aiimage/ChineseStopWords.txt') as f:
            for _ in f:
                stopwords.append(_.strip())
        words = jieba.cut(text)
        counter = Counter()
        for _word in words:
            if _word in stopwords:
                continue
            if len(_word) > 1 and _word != '\r\n':
                counter[_word] += 1
        print('常用词频度统计结果')
        for (_word, _count) in counter.most_common(20):
            print('%s%s %s  %d' % ('  ' * (5 - len(_word)), _word, '*' * int(_count / 3), _count))
        return counter.most_common(100)

    def ___get_words3(self, text):
        """
        tfidf 分词
        :param text:
        :return:
        """
        jieba.analyse.set_stop_words('aiimage/ChineseStopWords.txt')
        a = jieba.analyse.extract_tags(text, topK=20, withWeight=True, allowPOS=())
        print(a)


if __name__ == '__main__':
    fire.Fire(Cron)

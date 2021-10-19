import gevent.monkey

gevent.monkey.patch_ssl()
import fire
import os
import traceback
import redis
import requests

from pyspider.helper.date import Date
from pyspider.config import config
from hupun.config import SYSTEM_ROBOT_TOKEN


class Cron:
    def monitor_spider_status(self):
        """
        监控爬虫服务的状态，如果服务停止运行了，则重启;
        1, 使用redis的连接状态来判断服务是否运行;
        :return:
        """
        try:
            print('开始监控爬虫服务是否在正常运行,时间:{}'.format(Date.now().format()))
            redis_host = config.get('redis', 'host')
            redis_port = config.get('redis', 'port')
            redis_db = config.get('redis', 'db')
            my_redis = redis.Redis(host=redis_host, port=redis_port, db=redis_db)
            my_redis.keys()
            print('爬虫服务在正常运行')
        except Exception as e:
            print('err details: {}'.format(e))
            print(traceback.format_exc())
            print('爬虫服务挂掉了,时间:{}'.format(Date.now().format()))
            # 重启supervisor
            os.system("supervisorctl restart crawler-pyspider")
            # 发送报警通知
            title = '爬虫服务异常'
            text = '爬虫服务异常,依赖的redis:{}连接失败,请检查具体原因!!!'.format(
                config.get('redis', 'host') + ':' + config.get('redis', 'port'))
            now = Date.now().format()
            robot_url = 'https://oapi.dingtalk.com/robot/send?access_token={}'.format(SYSTEM_ROBOT_TOKEN)
            send_text = """# {title}
```
{time}
{content}
```     
        """.format(title=title, time=now, content=text)
            data = {"msgtype": "markdown", "markdown": {"title": title, "text": send_text},
                    "at": {"atMobiles": [], "isAtAll": False}}
            req = requests.post(robot_url, json=data)
            print('已发送报警通知:{}'.format(req.text))


if __name__ == '__main__':
    fire.Fire(Cron)

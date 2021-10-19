import asyncio

import aiohttp
import fire
import requests
import time

from ip_proxy.config import *
from pyspider.helper.date import Date
from pyspider.helper.ips_pool import IpRedis


class Cron:
    def update_proxy_ip(self):
        """
        更新代理
        :return:
        """
        index = 0
        api_url = 'http://proxy.httpdaili.com/apinew.asp?sl=10&noinfo=true&ddbh=302094241791519942'
        print("获取本次的 http 代理IP")

        while True:
            now = Date.now().format()
            print('第: {} 次更新代理, time: {}'.format(index, now))
            try:
                loop = asyncio.get_event_loop()
                ips = requests.get(api_url, timeout=10).text
                ip_list = ips.split('\r\n')[:-1]
                tasks = []
                for i in ip_list:
                    ip_split = i.split(':')
                    host = ip_split[0]
                    port = ip_split[1]
                    the_ip = host + ':' + port
                    tasks.append(self._get_ip_result(the_ip))
                    print("拿到了代理IP: {}".format(the_ip))
                if tasks:
                    loop.run_until_complete(asyncio.wait(tasks))
            except Exception as e:
                print('本次的代理IP获取失败：{}'.format(e))
            if index < EXECUTE_TIMES:
                index += 1
                time.sleep(INTERVAL_TIME)
            else:
                break

    def check_all_ip(self):
        """
        轮询检查所有的代理IP，剔除失效的IP
        :return:
        """
        index = 0
        while True:
            print('第: {} 次轮询检查所有代理IP'.format(index))
            ips = IpRedis().all()
            loop = asyncio.get_event_loop()
            tasks = []
            if ips:
                for _ip in ips:
                    tasks.append(self._get_ip_result(_ip))
            if tasks:
                loop.run_until_complete(asyncio.wait(tasks))
            if index < EXECUTE_TIMES:
                index += 1
                time.sleep(INTERVAL_TIME)
            else:
                break

    async def _get_ip_result(self, proxy_ip):
        """
        异步测试IP是否可用
        :param proxy_ip:
        :return:
        """
        conn = aiohttp.TCPConnector(verify_ssl=False)
        async with aiohttp.ClientSession(connector=conn) as session:
            try:
                if isinstance(proxy_ip, bytes):
                    proxy_ip = proxy_ip.decode('utf-8')
                real_proxy = 'http://' + proxy_ip
                print('正在测试', proxy_ip)
                async with session.get(IP_TEST_URL, proxy=real_proxy, timeout=10) as response:
                    if response.status in VALID_STATUS_CODE:
                        print('IP: {}可用,写入IP池'.format(proxy_ip))
                        IpRedis().add(proxy_ip)
                    else:
                        print('返回了错误的响应吗', proxy_ip)
                        IpRedis().delete(proxy_ip)
            except Exception as e:
                print('IP: {}不可用,删除该IP: {}'.format(proxy_ip, e))
                IpRedis().delete(proxy_ip)


if __name__ == '__main__':
    fire.Fire(Cron)

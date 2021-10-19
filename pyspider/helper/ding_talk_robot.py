import requests

ERP_AND_SPIDER = 'https://oapi.dingtalk.com/robot/send?access_token=bc697b1e919858d204c1e5722aa1f9c1c5e7f5ab81c7dd92b73722346296b484'

class DingTalkRobot:
    """
    钉钉群自定义机器人
    官方文档
    https://open-doc.dingtalk.com/docs/doc.htm?spm=a219a.7629140.0.0.z5MWoh&treeId=257&articleId=105735&docType=1
    """

    def __init__(self):
        self.webhook = ERP_AND_SPIDER

    def set_webhook(self, webhook):
        self.webhook = webhook

    def set_text(self, text):
        data = {"msgtype": "markdown", "markdown": {"title": '爬虫数据报警', "text": text}, "at": {"isAtAll": True}}
        requests.post(self.webhook, json=data)

    def send_markdown(self, title, trace):
        text = """# %s
```
%s
```
        """ % (title, trace)
        data = {"msgtype": "markdown", "markdown": {"title": title, "text": text}, "at": {"atMobiles": [], "isAtAll": False}}
        r = requests.post(self.webhook, json=data)

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import parseaddr, formataddr

from pyspider.helper.date import Date
from pyspider.helper.logging import logger
from pyspider.config import config


class EmailSender:
    """
    发送邮件
    """

    def __init__(self):
        self.my_user_list = []
        self.file_path_list = []
        self.mail_content = ""
        self.title = ""

    def set_receiver(self, receiver):
        """
        设置邮件的接收人
        :param receiver:
        :return:
        """
        if receiver not in self.my_user_list:
            self.my_user_list.append(receiver)
        return self

    def set_file_path(self, file_path):
        """
        添加附件(可添加多个附件)
        :param file_path: 附件的全路径地址, eg. /tmp/study/learn.csv
        :return:
        """
        if file_path not in self.file_path_list:
            self.file_path_list.append(file_path)
        return self

    def set_mail_content(self, content):
        """
        添加邮件正文
        :param content:
        :return:
        """
        self.mail_content = content
        return self

    def set_mail_title(self, title):
        """
        添加邮件的标题
        :param title:
        :return:
        """
        self.title = title
        return self

    def format_addr(self, msg):
        """
        格式化地址，为了支持中文
        :param msg:
        :return:
        """
        name, addr = parseaddr(msg)
        return formataddr((Header(name, 'utf-8').encode(), addr))

    def attachments_to_email(self, message):
        """
        把附件添加到邮件中
        :param message:
        :return:
        """
        if self.file_path_list:
            for file_path in self.file_path_list:
                if os.path.exists(file_path):
                    logger.info("File exists：{}".format(file_path))
                    # 构造附件，path路径下的文件
                    with open(file_path, 'rb') as f:
                        att = MIMEText(f.read(), 'base64', 'utf-8')
                        att["Content-Type"] = 'application/octet-stream'
                        # 这里的filename可以任意写，写什么名字，邮件中显示什么名字
                        att["Content-Disposition"] = 'attachment; filename="{}"'.format(f.name)
                        message.attach(att)
                else:
                    logger.info("File does not exist：{}".format(file_path))

    def send_email(self):
        """
        发送邮件模块
        :return:
        """
        # 发送邮件
        try:
            # 收件人为空，则不发送邮件
            if not self.my_user_list:
                logger.warn("No recipient, the message will not be sent")
                return
            # 判断收件人的地址是否正确
            for receiver in self.my_user_list:
                if '@' not in receiver:
                    logger.warn("The recipient's email is incorrect")
                    return

            now = Date().now().format()
            my_sender = config.get("email", "sender_username")
            my_pass = config.get("email", "sender_pwd")
            smtp_host = config.get("email", "smtp_host_qq")
            smtp_port = int(config.get("email", "smtp_port_qq"))

            # 创建邮件的实例
            message = MIMEMultipart()
            message['From'] = self.format_addr('ICY后台服务通知 <{}>'.format(my_sender))
            message['To'] = self.format_addr('相关处理人员 <{}>'.format(self.my_user_list))
            message['Subject'] = Header('{},时间:{}'.format(self.title, now), 'utf-8').encode()

            # 邮件正文内容
            message.attach(MIMEText(self.mail_content, 'plain', 'utf-8'))

            # 添加附件(可添加多个附件)
            self.attachments_to_email(message)

            # 发送邮件
            server = smtplib.SMTP_SSL(smtp_host, smtp_port)
            server.login(my_sender, my_pass)
            server.sendmail(my_sender, self.my_user_list, message.as_string())
            server.quit()
            logger.info("Mail sent successfully")
        except Exception as e:
            logger.exception("Send mail error details：{}".format(e))

import time

from alarm.config import HUPUN_SYNC_ABNORMAL_ROBOT
from alarm.helper import Helper
from alarm.page.ding_talk import DingTalk
from hupun_slow_crawl.model.es.goods_categories import GoodsCategories
from hupun.page.category.goods_categories_append import GoodsCategoryAppend
from hupun_slow_crawl.page.goods_categories_data import GoodsCategoriesData
from hupun.page.category.goods_categories_edit import GoodsCategoryEdit
from mq_handler.base import Base
from pyspider.helper.email import EmailSender


class CategoryUpdate(Base):
    """
    更新(添加，编辑)erp的类目数据
    """

    def execute(self):
        print('consume category update operation')
        self.print_basic_info()
        data = self._data
        parent_id = data.get('erpParentId', '')
        name = data.get('name', '')
        uid = data.get('erpGoodsCategoryId', '')
        # 写入数据
        if uid:
            # 编辑(edit)操作
            GoodsCategoryEdit(data, self._data_id, uid, parent_id, name) \
                .set_priority(GoodsCategoryEdit.CONST_PRIORITY_TOP) \
                .set_cookie_position(1) \
                .enqueue()
            time.sleep(10)
            # 发起强制更新商品列表的操作
            GoodsCategoriesData('-1') \
                .set_priority(GoodsCategoriesData.CONST_PRIORITY_TOP) \
                .set_cookie_position(1) \
                .enqueue()
            time.sleep(10)
            # 判断是否成功更新列表
            uid = ''  # 让uid置空，为了以名字查询结果
            if str(parent_id) == '-1':
                parent_id = ''
            result = GoodsCategories().has_catetory(parent_id, name, uid)
            if not result:
                if not Helper.in_project_env():
                    print('万里牛类目在编辑操作之后，没有查找到名为: {} 的类目, 测试环境, 不报警'.format(name))
                else:
                    # 报警
                    print('报警')
                    # 发送失败的消息
                    title = '万里牛类目的编辑操作失败'
                    err_msg = '在编辑操作之后，没有查找到名为: {} 的类目'.format(name)
                    ding_msg = '万里牛类目的编辑操作失败详情: {}, parent_id: {}, uid: {}'.format(err_msg, parent_id, uid)
                    DingTalk(HUPUN_SYNC_ABNORMAL_ROBOT, title, ding_msg).enqueue()
                    # 同时发送邮件通知
                    if data.get('email'):
                        EmailSender() \
                            .set_receiver(data.get('email')) \
                            .set_mail_title(title) \
                            .set_mail_content(ding_msg) \
                            .send_email()

        else:
            # 创建(append)操作
            uid = -1
            GoodsCategoryAppend(data, self._data_id, uid, parent_id, name) \
                .set_priority(GoodsCategoryAppend.CONST_PRIORITY_TOP) \
                .set_cookie_position(1) \
                .enqueue()
            time.sleep(10)
            # 发起强制更新商品列表的操作
            GoodsCategoriesData('-1') \
                .set_priority(GoodsCategoriesData.CONST_PRIORITY_TOP) \
                .set_cookie_position(1) \
                .enqueue()
            # 延长更新商品列表操作的等待时间
            time.sleep(60)
            # 把变量赋空值以便查询新增的类目
            uid = ''
            if str(parent_id) == '-1':
                parent_id = ''
            # 判断是否成功更新列表
            result = GoodsCategories().has_catetory(parent_id, name, uid)
            if not result:
                if not Helper.in_project_env():
                    print('万里牛类目的创建操作没有查找到名为: {} 的类目, 测试环境, 不报警'.format(name))
                else:
                    # 报警
                    print('报警')
                    # 发送失败的消息
                    title = '万里牛类目的创建操作失败'
                    err_msg = '在创建操作之后，没有查找到名为: {} 的类目'.format(name)
                    ding_msg = '万里牛类目的创建操作失败详情: {}, parent_id: {}, uid: {}'.format(err_msg, parent_id, uid)
                    DingTalk(HUPUN_SYNC_ABNORMAL_ROBOT, title, ding_msg).enqueue()
                    # 同时发送邮件通知
                    if data.get('email'):
                        EmailSender() \
                            .set_receiver(data.get('email')) \
                            .set_mail_title(title) \
                            .set_mail_content(ding_msg) \
                            .send_email()

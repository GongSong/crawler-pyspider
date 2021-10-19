import unittest

from backstage_data_migrate.page.file_download.download_base import DownloadBase
from backstage_data_migrate.page.jingdong_flow_data import JDFlowData
from backstage_data_migrate.page.manager_soft_export_log import ManagerSoftExLog
from backstage_data_migrate.page.redbook_download_data_goods import RedbookGoodsDown
from backstage_data_migrate.page.redbook_download_data_shop import RedbookShopDown
from backstage_data_migrate.page.sycm.sycm_all_goods_flow import SycmAllGoodsFlow
from pyspider.helper.date import Date
from backstage_data_migrate.page.jingdong_product_detail import JDProdictDetail
from backstage_data_migrate.page.jingdong_trade import JDTrade
from backstage_data_migrate.page.jingdong_view_flow import JDViewFlow
from backstage_data_migrate.page.redbook_databoard_msg import RedBookDataBoardMsg
from backstage_data_migrate.page.redbook_flow_data import RedbookFlowData
from backstage_data_migrate.page.redbook_visitor_msg import RedbookVisitorMsg
from backstage_data_migrate.page.sycm.sycm_tmall_databoard_msg import SycmTmallDataBoardMsg
from backstage_data_migrate.page.sycm.sycm_tmall_taobao_flow import SycmTmallTaobaoFlow
from backstage_data_migrate.page.sycm.sycm_tmall_visitor_msg import SycmTmallVisitorMsg
from backstage_data_migrate.page.sycm.sycm_yesterday_tmall_taobao_data import SycmYesterdayTmallTaobaoData
from cookie.model.data import Data
from pyspider.libs.oss import oss


class Test(unittest.TestCase):
    # 测试之前必须先更新cookie
    def _test_sycm_yesterday_data(self):
        """
        生意参谋昨天的天猫淘宝后台数据获取
        :return:
        """
        start_time = Date.now().plus_days(-1).format(full=False)
        end_time = start_time
        assert SycmYesterdayTmallTaobaoData('day', start_time, end_time, '流量看板', Data.CONST_USER_SYCM_BACKSTAGE[0][0],
                                            Data.CONST_USER_SYCM_BACKSTAGE[0][2]).test()

    def _test_sycm_today_data(self):
        """
        抓取生意参谋今天的数据，包括流量看板数据和访客数据
        :return:
        """
        assert SycmTmallDataBoardMsg(Data.CONST_USER_SYCM_BACKSTAGE[0][0], Data.CONST_USER_SYCM_BACKSTAGE[0][2]).test()
        assert SycmTmallVisitorMsg(Data.CONST_USER_SYCM_BACKSTAGE[0][0], Data.CONST_USER_SYCM_BACKSTAGE[0][2]).test()

    def _test_sycm_flow_data(self):
        """
        生意参谋的天猫淘宝流量来源的数据获取
        :return:
        """
        yesterday = Date.now().plus_days(-1).format(full=False)
        # pc
        assert SycmTmallTaobaoFlow(1, 'day', yesterday, yesterday, Data.CONST_USER_SYCM_BACKSTAGE[0][0]).test()
        # wifi
        assert SycmTmallTaobaoFlow(2, 'day', yesterday, yesterday, Data.CONST_USER_SYCM_BACKSTAGE[0][0]).test()

    def _test_sycm_all_goods_flow(self):
        """
        获取生意参谋 全量商品 的流量数据
        :return:
        """
        username, pwd, channel = Data.CONST_USER_SYCM_BACKSTAGE[1]
        start_day = Date.now().plus_days(-1).format(full=False)
        end_day = Date.now().plus_days(-1).format(full=False)
        SycmAllGoodsFlow(channel, 'all_device', 'day', start_day, end_day, username).test()

    def _test_taobao_manager_soft_export_log(self):
        """
        导出掌柜软件的商品数据日志查询
        :return:
        """
        account, password = Data.CONST_USER_TAOBAO_MANAGER_SOFT[0]
        compare_words = '出售中的宝贝+所有等待上架的，导出字段：宝贝ID/淘宝类目/货号/商家编码'
        the_date = Date.now().plus_hours(-2).format()
        ManagerSoftExLog(account, the_date, compare_words).test()

    def _test_redbook_data(self):
        """
        获取小红书的数据，包括流量看板数据和访客数据
        :return:
        """
        yesterday = Date.now().plus_days(-1).format(full=False)
        assert RedBookDataBoardMsg(yesterday, Data.CONST_USER_REDBOOK_BACKSTAGE[0][0]).test()
        assert RedbookVisitorMsg(yesterday, Data.CONST_USER_REDBOOK_BACKSTAGE[0][0]).test()

    def _test_redbook_flow_data(self):
        """
        获取小红书流量来源数据
        :return:
        """
        assert RedbookFlowData(Data.CONST_USER_REDBOOK_BACKSTAGE[0][0]).test()

    def _test_redbook_download_data(self):
        """
        获取小红书代购商家的商品流量表格数据下载
        :return:
        """
        day = 1
        assert RedbookGoodsDown(Data.CONST_USER_REDBOOK_BACKSTAGE[0][0], day).test()
        assert RedbookShopDown(Data.CONST_USER_REDBOOK_BACKSTAGE[0][0], day).test()

    def _test_jingdong_data(self):
        """
        获取京东数据
        :return:
        """
        yesterday = Date.now().plus_days(-1).format(full=False)
        assert JDProdictDetail(yesterday, yesterday, yesterday, '商品概况-day', Data.CONST_USER_JD_BACKSTAGE).test()
        assert JDTrade(yesterday, yesterday, yesterday, '交易概况-day', Data.CONST_USER_JD_BACKSTAGE).test()
        assert JDViewFlow(yesterday, yesterday, yesterday, '流量概况-day', Data.CONST_USER_JD_BACKSTAGE).test()

    def _test_jingdong_flow_data(self):
        """
        获取京东流量来源数据
        :return:
        """
        yesterday = Date.now().plus_days(-1).format(full=False)
        assert JDFlowData('day', 'app', yesterday, yesterday, yesterday, Data.CONST_USER_JD_BACKSTAGE).test()
        assert JDFlowData('day', 'pc', yesterday, yesterday, yesterday, Data.CONST_USER_JD_BACKSTAGE).test()
        assert JDFlowData('day', 'wechat', yesterday, yesterday, yesterday, Data.CONST_USER_JD_BACKSTAGE).test()
        assert JDFlowData('day', 'mobileq', yesterday, yesterday, yesterday, Data.CONST_USER_JD_BACKSTAGE).test()
        assert JDFlowData('day', 'mport', yesterday, yesterday, yesterday, Data.CONST_USER_JD_BACKSTAGE).test()

    def _test_download(self):
        url = 'http://www.baidu.com'
        start_time = Date.now().format(full=False)
        end_time = Date.now().format(full=False)
        file_path = oss.get_key(
            oss.CONST_TAOBAO_MANAGER_SOFT_PATH,
            '{words}/掌柜软件:{start_time}--{end_time}.xls'.format(
                words='test',
                start_time=start_time,
                end_time=end_time
            )
        )
        table_type = 'sheet'
        DownloadBase(url) \
            .set_table_type(table_type) \
            .set_oss_path(file_path) \
            .test()


if __name__ == '__main__':
    unittest.main()

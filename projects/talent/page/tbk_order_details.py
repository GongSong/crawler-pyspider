from talent.page.base_download import BaseDownload


class TbkOrderDetails(BaseDownload):
    """
    联盟商家中心，成交订单明细；
    来源地址：https://ad.alimama.com/report/overview/orders.htm?startTime=2020-02-12&endTime=2020-02-12&pageNo=1&jumpType=0&positionIndex=
    """
    URL = 'https://ad.alimama.com/report/downLoadTkTrans.do?status=3'

    def __init__(self, start_time, end_time, account, channel, upload=False):
        super(TbkOrderDetails, self).__init__(self.URL, start_time, end_time, account, channel, upload)

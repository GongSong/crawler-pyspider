from talent.page.base_download import BaseDownload


class Tbk(BaseDownload):
    URL = 'https://pub.alimama.com/report/getTbkOrderDetails.json?downloadId=DOWNLOAD_REPORT_ORDER_DETAILS&queryType=2&tkStatus=&memberType='

    def __init__(self, start_time, end_time, account, channel):
        super(Tbk, self).__init__(self.URL, start_time, end_time, account, channel)

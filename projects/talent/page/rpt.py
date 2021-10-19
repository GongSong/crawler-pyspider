from talent.page.base_download import BaseDownload


class Rpt(BaseDownload):
    URL = 'https://pub.alimama.com/report/selfRpt.json?DownloadID=DOWNLOAD_REPORT_REBORN_DETAIL&adzoneId='

    def __init__(self, start_time, end_time, account, channel):
        super(Rpt, self).__init__(self.URL, start_time, end_time, account, channel)

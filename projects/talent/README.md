# 达人的淘客订单爬虫

```
1. 每天登录到阿里妈妈后台
2. 下载淘宝客表格
3. 下载广告位表格
4. 把表格上传到ai web后台
5. 根据ai web后台上传返回的错误信息通知钉钉群
```

## url列表:

- name: url名称(英文，单词间下划线分割)
- url: url地址，必填
- params: 动态参数,
- description: url描述,

| name         | params                        | url                                                                                                                   | description |
|:-------------|:------------------------------|:----------------------------------------------------------------------------------------------------------------------|:------------|
| rpt          | start_time, end_time, account | https://pub.alimama.com/report/selfRpt.json?DownloadID=DOWNLOAD_REPORT_REBORN_DETAIL&adzoneId=                        | 广告位表格    |
| tbk          | start_time, end_time, account | https://pub.alimama.com/report/getTbkPaymentDetails.json?queryType=1&payStatus=&DownloadID=DOWNLOAD_REPORT_INCOME_NEW | 淘宝客表格    |
| upload_to_ai | file_path                     | https://10.0.5.62/api/admin/talent/upload_taobaoke                                                                    | 上传到ai后台  |

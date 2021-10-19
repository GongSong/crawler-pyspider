# 后台流量看板数据爬虫，包括京东、生意参谋、小红书

```
1. 获取cookie
2. 下载数据表格
3. 数据保存分为两种方式，Excel格式的分别在redis和oss中保存，其他数据保存到MongoDB中
```

## url列表:

- name: url名称(英文，单词间下划线分割)
- url: url地址，必填
- params: 动态参数,
- description: url描述,

| name                              | params                                                                   | url                                                                                                                                                                           | description         |
|:----------------------------------|:-------------------------------------------------------------------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:--------------------|
| jingdong_flow_data                | date_type, device, start_date, end_date, type_date, username             | https://sz.jd.com/viewflow/exportMyAttentionSourceData.ajax#{}                                                                                                                | 京东流量数据          |
| jingdong_product_detail           | date, end_date, start_date, date_type_name, username, retry              | https://sz.jd.com/productDetail/getProductSummary.ajax?channel=99&cmpType=0&date={date}&endDate={end_date}&startDate={start_date}&type=0#{random_id}                          | 京东商品概况数据       |
| jingdong_trade                    | date, end_date, start_date, date_type_name, username, retry              | https://sz.jd.com/trade/getSummaryData.ajax?channel=99&cmpType=0&date={date}&endDate={end_date}&startDate={start_date}#{random_id}                                            | 京东交易概况数据       |
| jingdong_view_flow                | date, end_date, start_date, date_type_name, username, retry              | https://sz.jd.com/viewflow/getCoreIndexData.ajax?cmpType=0&date={date}&endDate={end_date}&startDate={start_date}#{random_id}                                                  | 京东流量概况数据       | 
| redbook_databoard_msg             | date, username, retry                                                    | https://ark.xiaohongshu.com/api/ark/chaos/trd/realtime/overall?current_date={date}#{random_id}                                                                                | 小红书流量看板数据     |
| redbook_flow_data                 | day, username                                                            | https://ark.xiaohongshu.com/api/ark/chaos/trd/seller/channel?last_days={date}                                                                                                 | 小红书流量来源数据     |         
| redbook_visitor_msg               | date, username, retry                                                    | https://ark.xiaohongshu.com/api/ark/chaos/trd/realtime/trend?type=1&current_date={date}&compared_date={date}#{random_id}                                                      | 小红书访客数据         |
| sycm_tmall_databoard_msg          | username, channel, retry                                                 | https://sycm.taobao.com/flow/new/live/guide/trend/overview.json?device=0#{random_id}                                                                                          | 生意参谋数据看板实时信息|
| sycm_tmall_taobao_flow            | device, date_type, start_time, end_time, username                        | https://sycm.taobao.com/flow/gray/excel.do?_path_=v3/excel/shop/source&device={device}&dateType={date_type}&dateRange={start_time}&#124;{end_time}&belong=all#{random_id}     | 生意参谋流量来源数据    |
| sycm_tmall_visitor_msg            | username, channel, retry                                                 | https://sycm.taobao.com/flow/new/live/guide/trend.json?device=0&indexCode=uv%2Cpv%2ColdUv%2CnewUv%2CavgPv&type=1#{random_id}                                                  | 生意参谋实时访客数据    |
| sycm_yesterday_tmall_taobao_data  | date_type, start_time, end_time, date_type_name, username, channel, retry| https://sycm.taobao.com/flow/new/guide/trend/overview.json?device=0&dateType={date_type}&dateRange={start_time}%7C{end_time}#{random_id}                                      | 生意参谋历史数据       |  

## 接口测试：

| name                    | params                                                                          | 接口示例（线上环境，本地测试ip改为127.0.0.1:5000, 参数括号中的内容为参数可选项）                                                                                  |
|:------------------------|:--------------------------------------------------------------------------------|:--------------------------------------------------------------------------------------------------------------------------------|
|  京东商品概况             | channel(jingdong), timestamp, data_type(商品概况-day/商品概况-week/商品概况-month) | http://10.0.5.58:5500/apis/backstage_data/data?channel=jingdong&timestamp=2019-02-11&data_type=商品概况-week                     |
|  京东流量概况             | channel(jingdong), timestamp, data_type(流量概况-day/流量概况-week/流量概况-month) | http://10.0.5.58:5500/apis/backstage_data/data?channel=jingdong&timestamp=2019-02-11&data_type=流量概况-week                     |
|  京东交易概况             | channel(jingdong), timestamp, data_type(交易概况-day/交易概况-week/交易概况-month) | http://10.0.5.58:5500/apis/backstage_data/data?channel=jingdong&timestamp=2019-02-11&data_type=交易概况-week                     |
|  天猫流量看板历史数据      | channel(tmall), timestamp, data_type(流量看板/流量看板-week/流量看板-month)        | http://10.0.5.58:5500/apis/backstage_data/data?channel=tmall&timestamp=2019-02-25&data_type=流量看板                             |
|  淘宝流量看板历史数据      | channel(taobao), timestamp, data_type(流量看板/流量看板-week/流量看板-month)       | http://10.0.5.58:5500/apis/backstage_data/data?channel=taobao&timestamp=2019-02-25&data_type=流量看板                            |
|  天猫实时访客数据         | channel(tmall), timestamp, data_type(流量看板/访客数)                             | http://10.0.5.58:5500/apis/backstage_data/data?channel=tmall&timestamp=2019-02-25&data_type=访客数                               |
|  淘宝实时访客数据         |  channel(taobao), timestamp, data_type(流量看板/访客数)                           | http://10.0.5.58:5500/apis/backstage_data/data?channel=taobao&timestamp=2019-02-25&data_type=访客数                              |
|  小红书实时流量看板数据    | channel(redbook), timestamp, data_type(流量看板)                                 | http://10.0.5.58:5500/apis/backstage_data/data?channel=redbook&timestamp=2019-02-25&data_type=流量看板                           |
|  小红书实时访客数         | channel(redbook), timestamp, data_type(访客数)                                   | http://10.0.5.58:5500/apis/backstage_data/data?channel=redbook&timestamp=2019-02-25&data_type=访客数                             |
|  小红书流量来源           | channel(redbook), timestamp, data_type(小红书流量来源)                            | http://10.0.5.58:5500/apis/backstage_data/data?channel=redbook:flow&timestamp=2019-02-25&data_type=小红书流量来源                 | 
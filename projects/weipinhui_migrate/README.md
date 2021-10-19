# 唯品会后台商品详情抓取爬虫

```
1. 公司机房的 Mac-Pro 每四个小时会执行一次获取唯品会后台的 cookie 的脚本
2. Mac-Pro 上的唯品会 cookie 脚本中的图片验证码识别概率为百分之20，连续失败 8 次之后会发送钉钉报警
3. 每 4 小时抓取近 5 天的后台商品数据，写入 es。
4. 每 24 小时抓取近 30 天的后台商品数据，写入 es。
```

## url列表:

- name: url名称(英文，单词间下划线分割)
- url: url地址，必填
- params: 动态参数,
- description: url描述,

| name         | params                                   | url                                                                                                                   | description          |
|:-------------|:-----------------------------------------|:----------------------------------------------------------------------------------------------------------------------|:---------------------|
| weipinhui    | pageSize, pageNumber, beginDate, endDate | http://compass.vis.vip.com/newGoods/details/getDetails?callback=jQuery331013021774393544217_1542274423837&brandStoreN | 唯品会后台里的商品数据  |
|              |                                          | ame=ICY&goodsCode=&sortColumn=goodsAmt&sortType=1&brandName=%E5%94%AF%E5%93%81%E4%BC%9AX%E8%AE%BE%E8%AE%A1%E5%B8%88%E |                      |
|              |                                          | 5%93%81%E7%89 '%8C%E7%B2%BE%E9%80%89%E4%B8%93%E5%9C%BA-20181105&sumType=1&optGroupFlag=0&warehouseFlag=0&analysisType |                      |
|              |                                          | =0&selectedGoodsInfo=vipshopPrice%2CorderGoodsPrice&mixBrand=0&dateMode=0&dateType=D&detailType=D&dailyDate=&brandTyp |                      |
|              |                                          | e=%E6%99%AE%E9%80%9A%E7%89%B9%E5%8D%96&goodsType=0&dateDim=0'                  

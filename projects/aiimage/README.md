# 智能选款图片库及公众号文章词频爬虫

---
基于mitm中间人攻击实现
1. 在macpro部署mitm服务
2. 客户端设置http代理到192.168.4.100:8888
3. 客户端安装ssl证书(http://mitm.it/)
4. 有目的去浏览要抓取的页面
5. 服务端会定时把客户端浏览过的数据，解析处理并保存到es, 供[ai后台](https://ai.ichuanyi.com/ai-admin/#/goodsData/imageList)使用

---

- [中间人代理服务](#中间人代理服务)
- [品牌图片处理](#品牌图片处理)
- [明星图片处理](#明星图片处理)
- [微信公众号文章处理](#微信公众号文章处理)

## 中间人代理服务

### [代码](mitm.py)
### 部署
macpro: /etc/supervisord/mitm.ini

## 品牌图片处理

### [代码](cron.py) sync_brand_to_ai
### 部署
macpro: crontab -l | grep sync-brand-to-ai
### 注意
品牌图片的处理是基于图片域名映射品牌名实现的，新增品牌的时候记得修改host_assoc这个dict

## 明星图片处理

### [代码](cron.py) sync_star_to_ai
### 部署
macpro: crontab -l | grep sync-star-to-ai
### 注意
明星图片抓的是deepfashion下的follow页面，所以新增品牌的时候要先关注对应的明星，然后通过访问关注页面下的瀑布流实现

## 微信公众号文章处理

### [代码](cron.py) wechat
### 部署
macpro: crontab -l | grep wechat
### 注意
公众号文章是基于微信搜狗实现的, 要抓相应文章先进入
https://weixin.sogou.com/
搜索相关公众号或者文章，点击文章详情

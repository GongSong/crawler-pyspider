# icy商品评论抓取的配置文件

# request config
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
TIMEOUT = 20
CONNECT_TIMEOUT = 5
ES_ADDRESS = 'http://10.0.5.251:12200'

# 已登陆的 cookie 对应的名字
TAOBAO_COMMENT_NAME = '炫时科技:comment:研发02'
TMALL_COMMENT_NAME = 'icy旗舰店:comment:开发02'

# icy 评论的获取时间区间，默认为 60 天
ICY_COMMENTS_START_DAYS = 60
ICY_COMMENTS_END_DAYS = 0

# 京东渠道的 icy 店铺 ID
JD_ICY_SHOP_ID = '607075'

# 调度等级
SCHEDULE_LEVEL_FIRST = 50
SCHEDULE_LEVEL_SECOND = 40

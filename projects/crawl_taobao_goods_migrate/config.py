# request config
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
GOODS_TIMEOUT = 15
GOODS_CONNECT_TIMEOUT = 15
GOODS_RATE_TIMEOUT = 60
GOODS_RATE_CONNECT_TIMEOUT = 60


# 公司的代理
COMPANY_PROXY = '10.20.0.74:3128'

# 全量更新时的容许最大队列数
MAX_ALL_INVENTORY = 300

# 入队延迟时间
QUEUE_DELAY_TIME = 60 * 2

# 需要爬取的店铺
CRAWL_SHOPS = {
    "150087712": "https://maimeng.tmall.com/category.htm?scene=taobao_shop&search=y&orderType=newOn_desc&pageNo={}",  # 麦檬官方旗舰店
    "63240547": "https://moco.tmall.com/category.htm?scene=taobao_shop&search=y&orderType=newOn_desc&pageNo={}",  # moco官方旗舰店
    "61600101": "https://jnby.tmall.com/category.htm?scene=taobao_shop&search=y&orderType=newOn_desc&pageNo={}",  # JNBY官方旗舰店
    "70235107": "https://dazzle.tmall.com/category.htm?scene=taobao_shop&search=y&orderType=newOn_desc&pageNo={}",  # DAZZLE地素
    "200155482": "https://cos.tmall.com/category.htm?scene=taobao_shop&search=y&orderType=newOn_desc&pageNo={}",  # COS官方旗舰店
}

# 店铺商品抓取的重复商品判定个数
REPEAT_GOODS_LIMIT = 10

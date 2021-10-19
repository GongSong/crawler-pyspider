# 后台数据抓取的配置文件

# request config
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
RETRY_TIMES = 3

# 请求的延时时间, 单位：s
DELAY_TIME = 3600

REDIS_HOST = '10.0.5.5'
REDIS_PORT = 5321
REDIS_DB_ID = 0

# 未获取到的文件的大小
EMPTY_EXCEL = 15000
ROBOT_TOKEN = '928f2190f0c66007335eff9fb25167a207aa435b0e2952525586c78bb604ed3d'
# 报警数量大的机器人
OUR_ROBOT_TOKEN = 'fc8096a75d4ef6f57a3b83c04e01ed1f87513b9a10ea95d2c09ae13975fe3236'

# 爬虫抓取的 deadline
HUONIU_TIME = 14
SYCM_TIME = 14

# 小红书类别
REDBOOK_SHOP_TYPE = '店铺'
REDBOOK_GOODS_TYPE = '商品'

# 生意参谋文件下载项目的配置
SYCM_DOWNLOAD_CHANNEL = 'sycm'  # 生意参谋
REDBOOK_DOWNLOAD_CHANNEL = 'redbook'  # 小红书

SYCM_DOWNLOAD_FILE_TYPE = 'goods_effect'  # 生意参谋的商品效果文件下载
REDBOOK_DOWNLOAD_FILE_TYPE = 'goods_effect'  # 的商品效果文件下载

# 掌柜软件的导出请求类型
CONS_EXPORT_VALID = 'validate'
CONS_EXPORT_START = 'start'

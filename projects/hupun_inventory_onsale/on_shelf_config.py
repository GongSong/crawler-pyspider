from pyspider.config import config

TMALL_SHOPNAME = '天猫'
REDBOOK_SHOPNAME = "小红书"
JD_SHOPNAME = "京东"
ICY_SHOPNAME = "穿衣助手"
VIP_SHOPNAME = '唯品会'

host = config.get('crm', 'host')
RB_SHELF_URL = host + '/xhs/changeSpuAvailable'
TM_OFF_SHELF_URL = host + '/tm/delisting'
TM_ON_SHELF_URL = host + '/tm/listing'
JD_SHELF_URL = host + '/jd/wareUpOrDown'
ICY_SHELF_RUL = 'https://icy.design/internal.php?method=goods.newBatchSetIsSoldOut'
ERP_ADD_ALLOCATE_URL = host + '/wln/changeBillAdd'

# 唯品会上下架url，state为0下架，1上架
VIP_SHELF_URL = 'http://nov-admin.vip.com/normal/updateMerState4Selected?state={}'

# 唯品会上下架状态查询url
VIP_SHELF_STATUS_URL = 'http://nov-admin.vip.com/normal/normalMerchandiseQuery'

# 唯品会库存量查询url
VIP_STOCK_URL = 'http://nov-admin.vip.com/normal/normalMerchandiseSync'

# 唯品会sku库存查询url
VIP_SKU_STOCK_URL = 'http://nov-admin.vip.com/normal/normalMerItemQuery'

# 唯品会获取jsessionid的url和headers
JSESSIONID_URL = 'https://nov-admin.vip.com/vendor/normal/normalMerchandise?t={0}' \
                 '&__token__=eyJ0b2tlbiI6IjkwNGZiZTM0YzAwMjgzMzE0ZGQwM2Y2ZGQyMTM0YzcyIiwidG9rZW4xIjoiZjA0MDQ3YjgxMTJkYjY2ZmE0NmRiMGQyOTJlZTkyM2QiLCJ2ZW5kb3JJZCI6IjI4NTI2IiwidXNlck5hbWUiOiJtaW4uaHVAeW91cmRyZWFtLmNjIiwidmVuZG9yQ29kZSI6IjYxMzYwNSIsInVzZXJJZCI6IjEwMTc4OSIsInZpc1Nlc3Npb25JZCI6ImN2dHVyM29jNDc2ZTIwcHFzNDYwa2htY3QyIiwiYXBwTmFtZSI6InZpc1BDIiwidmlzaXRGcm9tIjoidmMifQ%3D%3D&{0}'

JSESSIONID_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36",
    "Content-Type": "application/json;charset=UTF-8",
}

TM_OFF_SHELF_ERROR = '当前时间段不允许做商品下架操作'

INVENTORY_TYPE_DICT = {
    '清除': -1,
    '实际库存': 0,
    '可用库存': 1,
    '在途库存': 4,
    '实际库存+在途库存': 2,
    '可用库存+在途库存': 3,
}

# 服务端的Redis配置
REDIS_HOST = '10.0.5.5'
REDIS_PORT = 5325
REDIS_DB = 0

# request config
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'

# 品牌的映射关系
brand_map = {
    'ICYPLUS': 1,
    'IDID': 2,
    'MUSNOVA': 3,
    'YES OR NO': 5,
    '线下其他设计师': 6,
    'ICY': 7,
}

# 设计来源的映射关系
design_source_map = {
    '自研': 1,
    '设计师联名': 2,
    '定向采购': 3,
    '设计师采购': 4,
    '设计师寄售': 5,
}

# 单位管理的映射关系
unit_map = {
    '件': 1,
    '条': 2,
    '套': 3,
    '个': 4,
    '对': 5,
    '双': 6,
}

# 钉钉报警机器人token
LANDONG_ROBOT_TOKEN = "8d67692c0106afe9379b44df67f9a0b4ecfc24a0fcdcfba4381bc334b550cdfc"

# 钉钉报警间隔时间 - 半天
WARNING_DELAY_TIME = 3600 * 12

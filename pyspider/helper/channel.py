channel_list = ['天猫', '京东', '小红书代购', 'app', '淘宝', '微信小程序']


def get_channel_dict():
    channel_dict = {}
    for _channel in channel_list:
        channel_dict.setdefault(_channel, [])
    return channel_dict


def get_channel_list():
    return channel_list


def get_channel(name):
    if name == 'wechat':
        return '微信小程序'
    return name


def channel_key_to_name(channel):
    channel_map = {
        'tmall': '天猫',
        'JD': '京东',
        'XHS': '小红书代购',
        'app': 'app',
        'taobao': '淘宝',
        'all': '全部'
    }
    return channel_map.get(channel, 'other')


def name_to_channel(channel):
    channel_map = {
        '天猫': 'tmall',
        '京东': 'JD',
        '小红书代购': 'XHS',
        'app': 'app',
        '淘宝': 'taobao',
        'wechat': 'app',
        '微信小程序': 'app',
    }
    return channel_map.get(channel, 'other')


def channel_to_names_list(channel):
    if channel == '天猫':
        return ['天猫']
    if channel == '京东':
        return ['京东']
    if channel == '小红书代购':
        return ['小红书代购']
    if channel == '淘宝':
        return ['淘宝']
    if channel == 'app':
        return ['app', 'wechat', '微信小程序']
    return []


def erp_name_to_shopuid(name):
    ''' 获取万里牛中店铺名对应的shopuid字段 '''
    shopuid_map = {
        '[天猫]icy旗舰店': 'D991C1F60CD5393F8DB19EADE17236F0',
        '[天猫]ICY奥莱': 'C91DC23F386A3A97BF61E2A673F20544',
        '[小红书]ICY小红书': '9A1C9BFF3C67302393D9BE60BB53B8EE',
        '[唯品会JIT]ICY唯品会': 'C9ACE29003EC3B9BB24D01FCFBBF6BE7',
        '[京东]穿衣助手旗舰店': '914E617DC96D3442BEC0B5E5844644BF',
        '[穿衣助手]iCY设计师集合店': '7F5259B8A03B37E686C00DD4E33562E5',
    }
    return shopuid_map.get(name, 'other')


def erp_name_to_tm_storekey(name):
    '''万里牛中店铺名称对应的天猫上下架接口storekey字段'''
    store_key_map = {
        '[天猫]icy旗舰店': 'icy',
        '[天猫]ICY奥莱': 'icyoutlets',
    }
    return store_key_map.get(name, 'other')

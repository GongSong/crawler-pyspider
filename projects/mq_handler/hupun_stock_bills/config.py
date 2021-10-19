from pyspider.config import config


def get_ding_token():
    env = config.get("app", "env")
    if env == "product":
        token = '87053027d1d9c2ca35b1eda6d248b3d087b764c135f1cb9b1b3387c47322d411'
    else:
        token = "3db2be0cf0858a6d590a2839469520552d7ed5bf67dbdcb2de2c5c960fef4bdb"
    return token

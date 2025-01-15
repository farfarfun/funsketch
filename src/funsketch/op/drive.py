from fundrive.drives.alipan import AliopenDrive, AlipanDrive
from fundrive.drives.baidu import BaiDuDrive
from fundrive.drives.webdav import WebDavDrive
from funsecret import read_secret
from funutil.cache import cache


def get_default_driv1():
    driver = BaiDuDrive()
    driver.login()
    return driver


@cache
def get_default_drive():
    driver = AlipanDrive()
    driver.login()
    return driver


def get_default_drive3():
    driver = WebDavDrive()
    driver.login(
        server_url=read_secret("funsketch", "webdav", "server_url"),
        username=read_secret(
            "funsketch",
            "webdav",
            "username",
        ),
        password=read_secret(
            "funsketch",
            "webdav",
            "password",
        ),
    )
    return driver

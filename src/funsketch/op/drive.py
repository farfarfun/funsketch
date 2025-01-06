from fundrive.drives.alipan import AlipanDrive
from fundrive.drives.baidu import BaiDuDrive
from fundrive.drives.webdav import WebDavDrive
from funsecret import read_secret


def get_default_drive3():
    driver = BaiDuDrive()
    driver.login()
    return driver


def get_default_drive2():
    driver = AlipanDrive()
    driver.login(is_resource=True)
    return driver


def get_default_drive():
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

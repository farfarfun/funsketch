from fundrive.core import BaseDrive
from fundrive.drives.alipan import AliopenDrive, AlipanDrive
from fundrive.drives.baidu import BaiDuDrive
from fundrive.drives.webdav import WebDavDrive
from funsecret import read_secret


def get_default_driv1() -> tuple[BaseDrive, BaseDrive]:
    """登录并返回两个指向同一百度网盘实例的驱动。"""
    driver = BaiDuDrive()
    driver.login()
    return driver, driver


def get_default_drive() -> tuple[BaseDrive, BaseDrive]:
    """登录并返回阿里云盘的文件驱动和开放平台驱动。

    每次调用都会重新登录，不做缓存：返回值携带认证状态且凭据/环境可能变化，
    使用无参数全局缓存会导致不同凭据或过期会话被错误地长期复用。
    """
    driver1 = AlipanDrive()
    driver1.login()
    drive2 = AliopenDrive()
    drive2.login()
    return driver1, drive2


def get_default_drive3() -> tuple[BaseDrive, BaseDrive]:
    """登录并返回两个指向同一 WebDAV 实例的驱动。"""
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
    return driver, driver

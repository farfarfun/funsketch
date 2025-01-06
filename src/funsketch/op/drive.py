from fundrive.drives.alipan import AlipanDrive
from fundrive.drives.baidu import BaiDuDrive


def get_default_drive():
    driver = BaiDuDrive()
    driver.login()
    return driver


def get_default_drive2():
    driver = AlipanDrive()
    driver.login(is_resource=True)
    return driver

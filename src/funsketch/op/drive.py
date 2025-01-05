from fundrive.drives.alipan import AlipanDrive


def get_default_drive():
    driver = AlipanDrive()
    driver.login(is_resource=True)
    return driver

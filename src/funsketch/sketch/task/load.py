import os

from fundrive.drives.baidu.drive import BaiDuDrive
from funsecret import read_cache_secret
from funsketch.sketch.meta import SketchMeta
from .base import BaseTask
from funutil import getLogger

logger = getLogger(__name__)


def longest_common_substring(strings):
    if not strings:
        return ""

    # 初始化第一个字符串
    base_string = strings[0]
    max_len = 0
    max_substr = ""

    # 遍历第一个字符串的所有子串
    for i in range(len(base_string)):
        for j in range(i + 1, len(base_string) + 1):
            substr = base_string[i:j]
            # 检查这个子串是否在所有字符串中
            if all(substr in s for s in strings):
                # 更新最长公共子串
                if len(substr) > max_len:
                    max_len = len(substr)
                    max_substr = substr

    return max_substr


class LoadTask(BaseTask):
    def __init__(self, bduss=None, stoken=None, ptoken=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        bduss = bduss or read_cache_secret("fundrive", "baidu", "bduss")
        stoken = stoken or read_cache_secret("fundrive", "baidu", "stoken")
        ptoken = ptoken or read_cache_secret("fundrive", "baidu", "ptoken")
        self.drive = BaiDuDrive()
        self.drive.login(bduss=bduss, stoken=stoken, ptoken=ptoken)

    def _run(self, sketch: SketchMeta, *args, **kwargs):
        self.success_file = os.path.join(sketch.result_video, "SUCCESS")
        path = f"/sketch/{sketch.name}"
        if not self.drive.exist(path):
            self.drive.save_shared(
                shared_url=sketch.shared_url, remote_dir="/sketch", password=sketch.pwd
            )
        os.makedirs(sketch.result_video, exist_ok=True)
        self.drive.download_dir(fid=path, local_dir=sketch.result_video)
        self.rename(sketch.result_video)

    def rename(self, path):
        files = [os.path.join(path, file) for file in os.listdir(path)]
        sizes = [len(file) for file in files]
        max_size = max(sizes)
        min_size = min(sizes)
        if min_size == max_size:
            logger.info("名称长度一样长")
            return
        common_name = longest_common_substring(files)
        logger.info("最长公共子串:", common_name)
        for old_name in files:
            new_name = (
                common_name
                + "0" * (max_size - len(old_name))
                + old_name.replace(common_name, "")
            )
            os.rename(old_name, new_name)

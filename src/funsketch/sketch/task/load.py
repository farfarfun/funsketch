import os
from typing import Any

from fundrive.drives.baidu.drive import BaiDuDrive
from funsecret import read_cache_secret
from farlog import getLogger

from .base import BaseTask

logger = getLogger("funsketch")


def longest_common_substring(strings: list[str]) -> str:
    """返回所有字符串共有的最长连续子串。"""
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
    """从百度网盘下载短剧视频并整理文件名。"""

    def __init__(
        self,
        bduss: str | None = None,
        stoken: str | None = None,
        ptoken: str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """使用指定凭据或缓存凭据初始化百度网盘驱动。"""
        super().__init__(*args, **kwargs)
        bduss = bduss or read_cache_secret("fundrive", "baidu", "bduss")
        stoken = stoken or read_cache_secret("fundrive", "baidu", "stoken")
        ptoken = ptoken or read_cache_secret("fundrive", "baidu", "ptoken")
        self.drive = BaiDuDrive()
        self.drive.login(bduss=bduss, stoken=stoken, ptoken=ptoken)
        self.success_file = os.path.join(self.sketch.result_video, "SUCCESS")

    def _run(self, *args: Any, **kwargs: Any) -> None:
        path = f"/sketch/{self.sketch.name}"
        if not self.drive.exist(path):
            self.drive.save_shared(
                shared_url=self.sketch.shared_url,
                remote_dir="/sketch",
                password=self.sketch.pwd,
            )
        os.makedirs(self.sketch.result_video, exist_ok=True)
        self.drive.download_dir(
            fid=path,
            local_dir=self.sketch.result_video,
            ignore_filter=lambda x: not x.endswith("mp4"),
            multi=True,
        )
        self.rename(self.sketch.result_video)

    def rename(self, path: str) -> None:
        """统一目录内文件名的数字部分宽度。"""
        files = [os.path.join(path, file) for file in os.listdir(path)]
        sizes = [len(file) for file in files]
        max_size = max(sizes)
        min_size = min(sizes)
        if min_size == max_size:
            logger.info("名称长度一样长")
            return
        common_name = longest_common_substring(files)
        logger.info("最长公共子串: {}", common_name)
        for old_name in files:
            new_name = (
                common_name
                + "0" * (max_size - len(old_name))
                + old_name.replace(common_name, "")
            )
            os.rename(old_name, new_name)

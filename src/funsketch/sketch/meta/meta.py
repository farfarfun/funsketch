import os

from farlog import getLogger

logger = getLogger("funsketch")


class SketchMeta:
    """保存短剧共享信息和本地处理目录。"""

    def __init__(
        self, shared_url: str, pwd: str, name: str, root: str = "./sketch_cache"
    ) -> None:
        """初始化短剧元数据及各阶段的结果路径。"""
        self.shared_url = shared_url
        self.pwd = pwd
        self.name = name
        self.root = f"{root}/{name}"
        self.result = os.path.join(self.root, "result")
        self.result_video = os.path.join(self.result, "video")
        self.result_audio = os.path.join(self.result, "audio")
        self.result_text = os.path.join(self.result, "text")
        logger.info(f"sketch name: {self.name}")
        logger.info(f"sketch root: {self.root}")

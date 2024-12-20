import os

from funutil import getLogger

logger = getLogger("funsketch")


class SketchMeta:
    def __init__(self, shared_url, pwd, name, root="./sketch_cache"):
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

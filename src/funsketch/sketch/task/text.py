import json
import os
from typing import Any

from funtalk.asr import WhisperASR
from farlog import getLogger

from .base import BaseTask

logger = getLogger("funsketch")


class TextTask(BaseTask):
    """将短剧音频识别为文本。"""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """初始化语音识别模型及成功标记路径。"""
        super().__init__(*args, **kwargs)
        self.success_file = os.path.join(self.sketch.result_text, "SUCCESS")
        self.model = WhisperASR("turbo")

    def _run(self, *args: Any, **kwargs: Any) -> None:
        os.makedirs(self.sketch.result_text, exist_ok=True)
        files = os.listdir(self.sketch.result_audio)
        files = sorted(files, key=lambda x: x)

        for file in files:
            textfile = os.path.join(
                self.sketch.result_text, file.replace(".wav", ".txt")
            )
            if not file.endswith(".wav"):
                continue
            if os.path.exists(textfile):
                logger.info(f"text file {textfile} already exists")
                continue
            audio_path = os.path.join(self.sketch.result_audio, file)
            result = self.model.transcribe(audio_path, language="zh")
            with open(textfile, "w", encoding="utf-8") as f:
                f.write(json.dumps(result))
            logger.success(f"{file} success")

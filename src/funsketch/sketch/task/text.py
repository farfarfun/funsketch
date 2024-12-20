import json
import os

import whisper
from funutil import getLogger

from .base import BaseTask

logger = getLogger("funsketch")


class TextTask(BaseTask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.success_file = os.path.join(self.sketch.result_text, "SUCCESS")

    def _run(self, *args, **kwargs):
        os.makedirs(self.sketch.result_text, exist_ok=True)
        files = os.listdir(self.sketch.result_audio)
        files = sorted(files, key=lambda x: x)
        model = whisper.load_model("turbo", device="cpu")
        for file in files:
            textfile = os.path.join(
                self.sketch.result_text, file.replace(".wav", ".txt")
            )
            if os.path.exists(textfile):
                logger.info(f"text file {textfile} already exists")
                continue
            audio_path = os.path.join(self.sketch.result_audio, file)
            result = model.transcribe(audio_path, language="zh", verbose=True)
            with open(textfile, "w", encoding="utf-8") as f:
                f.write(json.dumps(result))

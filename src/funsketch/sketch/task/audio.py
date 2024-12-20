import os

from funsketch.sketch.meta import SketchMeta
from .base import BaseTask
from funutil import getLogger
from moviepy import VideoFileClip

logger = getLogger(__name__)


class AudioTask(BaseTask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def run(self, sketch: SketchMeta, *args, **kwargs):
        os.makedirs(sketch.result_audio, exist_ok=True)
        files = os.listdir(sketch.result_video)
        files = sorted(files, key=lambda x: x)
        for file in files:
            filepath = os.path.join(sketch.result_video, file)
            if not filepath.endswith(".mp4"):
                continue
            video_path = filepath

            # 指定输出音频文件路径
            audio_path = os.path.join(sketch.result_audio, file.replace(".mp4", ".wav"))
            if os.path.exists(audio_path):
                logger.info(f"audio file {audio_path} already exists")
                continue
            video_clip = VideoFileClip(video_path)
            audio_clip = video_clip.audio
            audio_clip.write_audiofile(audio_path)
            audio_clip.close()
            video_clip.close()

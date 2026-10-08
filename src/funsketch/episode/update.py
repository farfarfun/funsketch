import json
import os
from typing import Any

from farlog import getLogger
from fundrive.core import BaseDrive
from funtalk.asr import WhisperASR
from moviepy import VideoFileClip
from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session

from funsketch.db import Episode

logger = getLogger("funsketch")


class EpisodePath:
    """根据分集记录计算本地视频/音频/文本的落盘路径。"""

    def __init__(self, episode: Episode) -> None:
        """根据分集信息初始化各阶段产物的本地路径，并创建所在目录。"""
        self.episode = episode
        self.sketch_dir = f"funsketch/{episode.sketch_id}"

        self.video_path = (
            f"{self.sketch_dir}/{str(episode.index).zfill(3)}-{episode.uid}.mp4"
        )
        self.audio_path = (
            f"{self.sketch_dir}/{str(episode.index).zfill(3)}-{episode.uid}.wav"
        )
        self.text_path = (
            f"{self.sketch_dir}/{str(episode.index).zfill(3)}-{episode.uid}.txt"
        )
        os.makedirs(self.sketch_dir, exist_ok=True)

    def download_video(self, driver: BaseDrive) -> None:
        """用给定的网盘驱动把分集视频下载到本地。"""
        driver.download_file(
            self.episode.fid,
            local_dir=self.sketch_dir,
            filepath=self.video_path,
            overwrite=False,
        )

    def convert_video(self, *args: Any, **kwargs: Any) -> None:
        """用 moviepy 从本地视频提取音频；音频已存在则跳过。"""
        if os.path.exists(self.audio_path):
            logger.info(f"audio file {self.audio_path} already exists")
            return
        video_clip = VideoFileClip(self.video_path)
        audio_clip = video_clip.audio
        audio_clip.write_audiofile(self.audio_path)
        audio_clip.close()
        video_clip.close()

    def detect_text(self) -> None:
        """用 Whisper 把本地音频转写为文本；文本已存在则跳过。"""
        if os.path.exists(self.text_path):
            logger.info(f"text file {self.text_path} already exists")
            return
        model = WhisperASR("turbo")
        result = model.transcribe(self.audio_path, language="zh")
        with open(self.text_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(result))
        logger.success(f"{self.text_path} success")


def update_episode(engine: Engine, drive: BaseDrive, *args: Any, **kwargs: Any) -> None:
    """对文本过短的分集逐条下载视频、提取音频、转写文本并回写数据库。"""
    with Session(engine) as session:
        episodes = session.execute(
            select(Episode).where(func.char_length(Episode.text) < 10)
        ).scalars()

        for episode in episodes:
            episode_path = EpisodePath(episode)
            episode_path.download_video(driver=drive)
            episode_path.convert_video()
            episode_path.detect_text()
            text_path = f"/{episode_path.text_path}"
            drive.upload_file(local_path=episode_path.text_path, fid=text_path)
            episode.text = text_path
            episode.upsert(session=session, update_data=True)
            session.commit()

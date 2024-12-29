import json
import os

from funtalk.asr import WhisperASR
from funutil import getLogger
from moviepy import VideoFileClip
from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session

from funsketch.db import Episode

logger = getLogger("funsketch")


class EpisodePath:
    def __init__(self, episode: Episode):
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

    def download_video(self, driver):
        driver.download_file(
            self.episode.fid,
            local_dir=self.sketch_dir,
            filepath=self.video_path,
            overwrite=False,
        )

    def convert_video(self, *args, **kwargs):
        if os.path.exists(self.audio_path):
            logger.info(f"audio file {self.audio_path} already exists")
            return
        video_clip = VideoFileClip(self.video_path)
        audio_clip = video_clip.audio
        audio_clip.write_audiofile(self.audio_path)
        audio_clip.close()
        video_clip.close()

    def detect_text(self):
        if os.path.exists(self.text_path):
            logger.info(f"text file {self.text_path} already exists")
            return
        model = WhisperASR("turbo")
        result = model.transcribe(self.audio_path, language="zh")
        with open(self.text_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(result))
        logger.success(f"{self.text_path} success")


def update_episode(engine: Engine, drive, *args, **kwargs):
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
            episode.upsert(session=session)
            session.commit()

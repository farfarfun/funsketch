import json
import os

from fundb.sqlalchemy.table import BaseTable
from funsecret import read_secret
from funtalk.asr import WhisperASR
from funutil import getLogger
from moviepy import VideoFileClip
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from funsketch.db import Episode, Sketch
from funsketch.db.analyse import Analyse
from funsketch.op.drive import get_default_drive

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


def update_text_episode(overwrite=False):
    driver1, driver2 = get_default_drive()
    engine = create_engine(read_secret("funsketch", "db", "url"), echo=False)
    BaseTable.metadata.create_all(engine)

    with Session(engine) as session:
        sketch_map = dict(
            [(t.uid, t.fid) for t in session.execute(select(Sketch)).scalars()]
        )

        video_sql = select(Episode)
        text_sql = select(Analyse).where(Analyse.folder == "text")
        episode2 = [t.episode_id for t in session.execute(text_sql).scalars()]

        if overwrite:
            episode2.clear()
        episodes = [
            t for t in session.execute(video_sql).scalars() if t.uid not in episode2
        ]

        if episodes is None or len(episodes) == 0:
            logger.success("all episonde analyse success.")
            return

        text_fid = driver1.mkdir(sketch_map[episodes[0].sketch_id], name="text")

        for episode in episodes:
            episode_path = EpisodePath(episode)
            episode_path.download_video(driver=driver2)
            episode_path.convert_video()
            episode_path.detect_text()
            driver1.upload_file(filedir=episode_path.text_path, fid=text_fid)

            name_dict = dict(
                [(file.name, file.fid) for file in driver2.get_file_list(text_fid)]
            )
            for episode in episodes:
                episode_path = EpisodePath(episode)
                text_name = os.path.basename(episode_path.text_path)
                if text_name in name_dict:
                    entity = Analyse(
                        sketch_id=episode.sketch_id,
                        episode_id=episode.uid,
                        fid=name_dict[text_name],
                        name=text_name,
                        folder="text",
                    )
                    entity.upsert(session=session)
                    session.commit()


update_text_episode()

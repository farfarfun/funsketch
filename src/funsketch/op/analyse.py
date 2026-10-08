import json
import os
from typing import Any

from fardb.sqlalchemy.table import BaseTable
from farlog import getLogger
from fundrive.core import BaseDrive
from funsecret import read_secret
from funtalk.asr import WhisperASR
from moviepy import VideoFileClip
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from funsketch.db import Episode, Sketch
from funsketch.db.analyse import Analyse
from funsketch.op.drive import get_default_drive

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


def update_text_episode(overwrite: bool = False) -> None:
    """同步网盘上未转写的分集：批量下载视频、转写文本并建立分析记录。"""
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

        sketch_id = episodes[0].sketch_id
        sketch_fid = sketch_map.get(sketch_id)
        if not sketch_fid:
            raise ValueError(f"分集所属短剧 {sketch_id} 未找到网盘目录")
        try:
            text_fid = driver1.mkdir(sketch_fid, name="text")
        except Exception as exc:
            raise RuntimeError(f"无法为短剧 {sketch_id} 创建文本目录") from exc

        for episode in episodes:
            episode_path = EpisodePath(episode)
            episode_path.download_video(driver=driver2)
            episode_path.convert_video()
            episode_path.detect_text()
            try:
                driver1.upload_file(filedir=episode_path.text_path, fid=text_fid)
            except Exception as exc:
                raise RuntimeError(
                    f"无法上传分集 {episode.uid} 的文本文件 {episode_path.text_path}"
                ) from exc

            try:
                files = driver1.get_file_list(text_fid)
            except Exception as exc:
                raise RuntimeError(
                    f"无法读取短剧 {sketch_id} 的文本目录 {text_fid}"
                ) from exc
            try:
                name_dict = {file.name: file.fid for file in files}
            except (AttributeError, TypeError) as exc:
                raise ValueError(
                    f"短剧 {sketch_id} 的文本目录 {text_fid} 返回了无效文件数据"
                ) from exc
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
                    entity.upsert(session=session, update_data=True)
                    session.commit()

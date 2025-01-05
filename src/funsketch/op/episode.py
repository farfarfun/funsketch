import json

from funai.llm import get_model
from fundb.sqlalchemy.table import BaseTable
from funsecret import read_secret
from funsketch.db import Episode, Sketch
from funutil import getLogger
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from funsketch.op.drive import get_default_drive

logger = getLogger("funsketch")


def sync_episode_data():
    drive = get_default_drive()
    model = get_model("deepseek")
    engine = create_engine(read_secret("funsketch", "db", "url"), echo=False)
    BaseTable.metadata.create_all(engine)
    with Session(engine) as session:
        res = BaseTable.select_all(session=session, table=Sketch)
        for sketch in res:
            data = [
                f'{data["fid"]}, name={data["name"]}'
                for data in drive.get_file_list(sketch.video_fid)
                if data["name"].endswith(".mp4")
            ]
            data = "\n".join([i for i in data])
            prompt = f"""
                下面是一部电视剧的所有文件路径，请分析这些文件名，返回视频顺序，要求返回结果是json的列表，包含path，index, name,只返回json，不要用```包含
                {data}
                """
            res = model.chat(prompt)
            res = json.loads(res)
            for data in res:
                episode = Episode(
                    fid=data["path"],
                    name=data["name"],
                    index=data["index"],
                    sketch_id=sketch.uid,
                )
                print(episode.to_dict())
                episode.upsert(session=session)
            session.commit()

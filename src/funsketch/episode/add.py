import json

from funai.llm import get_model
from fundb.sqlalchemy.table import BaseTable
from fundrive.drives.baidu.drive import BaiDuDrive
from funsecret import read_secret
from funutil import getLogger
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from funsketch.db import Episode, Sketch

logger = getLogger("funsketch")

model = get_model("deepseek")


def sync_episode_from_sketch(
    engine: Engine, bduss=None, stoken=None, ptoken=None, *args, **kwargs
):
    bduss = bduss or read_secret("fundrive", "baidu", "bduss")
    stoken = stoken or read_secret("fundrive", "baidu", "stoken")
    ptoken = ptoken or read_secret("fundrive", "baidu", "ptoken")
    drive = BaiDuDrive()
    drive.login(bduss=bduss, stoken=stoken, ptoken=ptoken)

    with Session(engine) as session:
        res = BaseTable.select_all(session=session, table=Sketch)
        for sketch in res:
            print(sketch.uid)
            data = [
                data["fid"]
                for data in drive.get_file_list(sketch.fid)
                if data["fid"].endswith(".mp4")
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
                episode.upsert(session=session)
            session.commit()

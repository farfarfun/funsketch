from fundrive.core import BaseDrive
from funsecret import read_secret
from funsketch.db import Sketch
from fundb.sqlalchemy.table import BaseTable
from funutil import getLogger
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from .drive import get_default_drive

logger = getLogger("funsketch")


def sync_sketch_data(
    driver: BaseDrive = None,
    sketch_fid="677a4bbc22c22185a94449fea7d7526e0905696d",
    funsketch_fid="677a78422552250db76c412c98b2c1d9b2779a58",
):
    driver = driver or get_default_drive()

    url = read_secret("funsketch", "db", "url")
    engine = create_engine(url, echo=False)
    BaseTable.metadata.create_all(engine)
    with Session(engine) as session:
        for file in driver.get_dir_list(sketch_fid):
            fid = driver.mkdir(fid=funsketch_fid, name=file["name"])
            sketch = Sketch(fid=fid, name=file["name"], video_fid=file.fid)
            sketch.upsert(session)
            session.commit()

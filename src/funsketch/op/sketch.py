from fundrive.core import BaseDrive
from funsecret import read_secret
from funsketch.db import Sketch
from funutil import getLogger
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

logger = getLogger("funsketch")


def sync_data(driver: BaseDrive):
    sketch_fid = "677a4bbc22c22185a94449fea7d7526e0905696d"
    funsketch_fid = "677a78422552250db76c412c98b2c1d9b2779a58"

    url = read_secret("funsketch", "db", "url")
    engine = create_engine(url, echo=False)
    with Session(engine) as session:
        for file in driver.get_dir_list(sketch_fid):
            fid = driver.mkdir(fid=funsketch_fid, name=file["name"])
            sketch = Sketch(fid=fid, name=file["name"])
            sketch.upsert(session)

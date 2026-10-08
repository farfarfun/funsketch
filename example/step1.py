from funsecret import read_secret
from funsketch.db.sketch import add_sketch
from funsketch.episode.update import update_episode
from funsketch.op.drive import get_default_drive
from farlog import getLogger
from sqlalchemy import create_engine

logger = getLogger("funsketch")

url = read_secret("funsketch", "db", "url")
engine = create_engine(url, echo=False)


def step1():
    drive, _ = get_default_drive()
    add_sketch(
        engine,
        name="替嫁侯府守活寡她赢麻了",
        fid="/sketch/替嫁侯府守活寡她赢麻了30",
        video_fid="/sketch/替嫁侯府守活寡她赢麻了30/video",
    )
    update_episode(engine=engine, drive=drive)


if __name__ == "__main__":
    step1()

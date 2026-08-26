from funsecret import read_secret
from funsketch.db import add_sketch, update_episode
from funutil import getLogger
from sqlalchemy import create_engine

logger = getLogger("funsketch")

url = read_secret("funsketch", "db", "url")
engine = create_engine(url, echo=False)


def step1():
    add_sketch(
        engine, name="替嫁侯府守活寡她赢麻了", fid="/sketch/替嫁侯府守活寡她赢麻了30"
    )
    update_episode(engine=engine)

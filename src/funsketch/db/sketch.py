from fundb.sqlalchemy.table import BaseTable
from funutil import getLogger
from sqlalchemy import Engine, String
from sqlalchemy.orm import Mapped, Session, mapped_column

logger = getLogger("funsketch")


class Sketch(BaseTable):
    __tablename__ = "sketch"
    name: Mapped[str] = mapped_column(String(128), comment="资源名称")
    video_fid: Mapped[str] = mapped_column(String(64), comment="视频文件夹", default="")
    fid: Mapped[str] = mapped_column(String(64), comment="资源文件夹", default="")

    def _get_uid(self):
        return self.name

    def _child(self):
        return Sketch

    def _to_dict(self):
        return {"name": self.name, "fid": self.fid, "video_fid": self.video_fid}


def add_sketch(engine: Engine, name, fid, video_fid):
    BaseTable.metadata.create_all(engine)
    with Session(engine) as session:
        Sketch(name=name, video_fid=video_fid, fid=fid).upsert(
            session=session, update_data=True
        )
        session.commit()

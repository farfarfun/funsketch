from fundb.sqlalchemy.table import BaseTable
from funutil import getLogger
from sqlalchemy import Engine, String
from sqlalchemy.orm import Mapped, Session, mapped_column

logger = getLogger("funsketch")


class Sketch(BaseTable):
    __tablename__ = "sketch"
    name: Mapped[str] = mapped_column(String(128), comment="资源名称")
    fid: Mapped[str] = mapped_column(String(64), comment="文件唯一ID", default="")

    def _get_uid(self):
        return self.fid

    def _child(self):
        return Sketch

    def _to_dict(self):
        return {"name": self.name, "fid": self.fid}


def add_sketch(engine: Engine, name, fid):
    BaseTable.metadata.create_all(engine)
    with Session(engine) as session:
        Sketch(name=name, fid=fid).upsert(session=session, update_data=True)
        session.commit()

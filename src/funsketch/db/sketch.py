from fardb.sqlalchemy.table import BaseTable
from farlog import getLogger
from sqlalchemy import Engine, String
from sqlalchemy.orm import Mapped, Session, mapped_column

logger = getLogger("funsketch")


class Sketch(BaseTable):
    """短剧资源表，保存短剧名称及其在网盘中的资源和视频目录标识。

    实例由 ``name``、``fid`` 和 ``video_fid`` 初始化；``_to_dict`` 返回这些字段
    及基类生成的唯一标识，供同步流程写入和读取。
    """

    __tablename__ = "sketch"
    name: Mapped[str] = mapped_column(String(128), comment="资源名称")
    video_fid: Mapped[str] = mapped_column(String(64), comment="视频文件夹", default="")
    fid: Mapped[str] = mapped_column(String(64), comment="资源文件夹", default="")

    def _get_uid(self) -> str:
        return self.name

    def _child(self) -> type["Sketch"]:
        return Sketch

    def _to_dict(self) -> dict:
        return {"name": self.name, "fid": self.fid, "video_fid": self.video_fid}


def add_sketch(engine: Engine, name: str, fid: str, video_fid: str) -> None:
    """写入或更新一部短剧的网盘目录信息。"""
    BaseTable.metadata.create_all(engine)
    with Session(engine) as session:
        Sketch(name=name, video_fid=video_fid, fid=fid).upsert(
            session=session, update_data=True
        )
        session.commit()

from fundb.sqlalchemy.table import BaseTable
from funutil import getLogger
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

logger = getLogger("funsketch")


class Analyse(BaseTable):
    __tablename__ = "analyse_detail"
    sketch_id: Mapped[str] = mapped_column(String(64), comment="文件唯一ID", default="")
    episode_id: Mapped[str] = mapped_column(String(64), comment="集", default="")
    folder: Mapped[str] = mapped_column(String(64), comment="文件夹", default="video")
    name: Mapped[str] = mapped_column(String(128), comment="资源名称")
    size: Mapped[int] = mapped_column(comment="大小", default=0)
    fid: Mapped[str] = mapped_column(String(64), comment="文件唯一ID", default="")
    text: Mapped[str] = mapped_column(String(1200), comment="视频文本", default="")

    def _get_uid(self):
        return f"{self.episode_id}:{self.folder}"

    def _child(self):
        return Analyse

    def _to_dict(self) -> dict:
        return {
            "sketch_id": self.sketch_id,
            "episode_id": self.episode_id,
            "name": self.name,
            "folder": self.folder,
            "size": self.size,
            "fid": self.fid,
            "text": self.text,
        }

import json

from funai.llm import get_model
from fardb.sqlalchemy.table import BaseTable
from funsecret import read_secret
from funsketch.db import Episode, Sketch
from farlog import getLogger
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from funsketch.op.drive import get_default_drive

logger = getLogger("funsketch")


def _parse_episode_response(response: str, sketch_id: str) -> list[dict]:
    """解析并校验模型返回的分集列表。"""
    try:
        data = json.loads(response)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"短剧 {sketch_id} 的分集模型响应不是合法 JSON: {response!r}"
        ) from exc

    if not isinstance(data, list):
        raise ValueError(f"短剧 {sketch_id} 的分集模型响应必须是 JSON 列表")

    for item in data:
        if not isinstance(item, dict):
            raise ValueError(f"短剧 {sketch_id} 的分集模型响应包含非对象条目: {item!r}")
        missing = {"path", "index", "name"} - item.keys()
        if missing:
            raise ValueError(
                f"短剧 {sketch_id} 的分集模型响应缺少字段: {', '.join(sorted(missing))}"
            )
        if not isinstance(item["path"], str) or not isinstance(item["name"], str):
            raise ValueError(f"短剧 {sketch_id} 的分集模型响应包含无效文件字段")
        if not isinstance(item["index"], int):
            raise ValueError(f"短剧 {sketch_id} 的分集模型响应包含无效分集序号")
    return data


def sync_episode_data() -> None:
    """同步网盘视频目录，使用模型推断剧集顺序并写入数据库。"""
    drive, _ = get_default_drive()
    model = get_model("deepseek")
    engine = create_engine(read_secret("funsketch", "db", "url"), echo=False)
    BaseTable.metadata.create_all(engine)
    with Session(engine) as session:
        res = BaseTable.select_all(session=session, table=Sketch)
        for sketch in res:
            try:
                files = drive.get_file_list(sketch.video_fid)
                data = [
                    f"{file['fid']}, name={file['name']}"
                    for file in files
                    if file["name"].endswith(".mp4")
                ]
            except (KeyError, TypeError) as exc:
                raise ValueError(
                    f"短剧 {sketch.uid} 的视频目录 {sketch.video_fid} 返回了无效文件数据"
                ) from exc
            except Exception as exc:
                raise RuntimeError(
                    f"无法读取短剧 {sketch.uid} 的视频目录 {sketch.video_fid}"
                ) from exc
            data = "\n".join([i for i in data])
            prompt = f"""
                下面是一部电视剧的所有文件路径，请分析这些文件名，返回视频顺序，要求返回结果是json的列表，包含path，index, name,只返回json，不要用```包含
                {data}
                """
            try:
                response = model.chat(prompt)
            except Exception as exc:
                raise RuntimeError(f"短剧 {sketch.uid} 的分集模型调用失败") from exc
            episodes = _parse_episode_response(response, sketch.uid)
            for data in episodes:
                episode = Episode(
                    fid=data["path"],
                    name=data["name"],
                    index=data["index"],
                    sketch_id=sketch.uid,
                )
                logger.info("已生成剧集: {}", episode.to_dict())
                episode.upsert(session=session)
            session.commit()

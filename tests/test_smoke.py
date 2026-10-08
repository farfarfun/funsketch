"""funsketch 的轻量测试。

涉及凭据、网盘、媒体处理和模型的流程均通过替身对象隔离，测试不会访问真实外部系统。
当前发布的 funfile 未提供 funget 导入的兼容模块，因此测试注册一个最小垫片以便完成导入。
"""

import hashlib
import json
import os
import runpy
import sys
import types
from types import SimpleNamespace

# 兼容 funget 与 funfile 当前发布版本之间的导入差异。
try:
    import funfile.compress as _funfile_compress

    if "funfile.compress.utils" not in sys.modules:
        _shim = types.ModuleType("funfile.compress.utils")
        _shim.file_tqdm_bar = _funfile_compress.file_tqdm_bar
        sys.modules["funfile.compress.utils"] = _shim
except ImportError:
    pass


def test_import_top_level_package():
    """顶层包导入时不应产生外部副作用。"""
    import funsketch  # noqa: F401


def test_import_db_module():
    """数据库模块导入时不需要凭据或网络。"""
    import funsketch.db as db

    assert db.__all__ == ["Sketch", "Episode", "Analyse"]


def test_import_op_module():
    """操作模块只应在函数调用时读取凭据。"""
    import funsketch.op as op

    assert set(op.__all__) == {
        "sync_sketch_data",
        "sync_episode_data",
        "update_text_episode",
    }


def test_import_episode_update_module():
    import funsketch.episode.update  # noqa: F401


def test_import_sketch_task_module():
    """任务模块应能借助兼容垫片正常导入。"""
    import funsketch.sketch.task as task

    assert set(task.__all__) == {
        "BaseTask",
        "LoadTask",
        "AudioTask",
        "TextTask",
        "TaskRun",
    }


def test_import_sketch_meta_module():
    import funsketch.sketch.meta as meta

    assert meta.__all__ == ["SketchMeta"]


def test_example_uses_importable_apis(monkeypatch):
    """示例引用的 API 应能在不读取真实凭据时完成导入。"""
    import funsecret
    import sqlalchemy

    monkeypatch.setattr(funsecret, "read_secret", lambda *_a: "sqlite:///:memory:")
    monkeypatch.setattr(sqlalchemy, "create_engine", lambda *_a, **_k: object())

    runpy.run_path("example/step1.py")


# 纯逻辑测试


def test_sketch_meta_paths_are_pure_string_building():
    """SketchMeta 初始化只构造路径，不执行 I/O。"""
    from funsketch.sketch.meta import SketchMeta

    meta = SketchMeta(
        shared_url="https://example.com/share",
        pwd="1234",
        name="my-drama",
        root="/tmp/sketch_cache_root",
    )

    assert meta.shared_url == "https://example.com/share"
    assert meta.pwd == "1234"
    assert meta.name == "my-drama"
    assert meta.root == "/tmp/sketch_cache_root/my-drama"
    assert meta.result == os.path.join(meta.root, "result")
    assert meta.result_video == os.path.join(meta.result, "video")
    assert meta.result_audio == os.path.join(meta.result, "audio")
    assert meta.result_text == os.path.join(meta.result, "text")


def test_sketch_meta_default_root():
    from funsketch.sketch.meta import SketchMeta

    meta = SketchMeta(shared_url="u", pwd="p", name="abc")
    assert meta.root == "./sketch_cache/abc"


def test_sync_sketch_data_with_fake_driver():
    """同步入口可用假的网盘驱动验证正常数据库路径。"""
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import Session

    from funsketch.db import Sketch
    from funsketch.op import sketch as sketch_op

    class FakeDrive:
        def get_dir_list(self, fid):
            return [SimpleNamespace(name="示例短剧", fid="source-fid")]

        def mkdir(self, fid, name):
            return "target-fid"

    engine = create_engine("sqlite:///:memory:")
    original_engine = sketch_op.create_engine
    original_secret = sketch_op.read_secret
    sketch_op.create_engine = lambda *_args, **_kwargs: engine
    sketch_op.read_secret = lambda *_args: "sqlite:///:memory:"
    try:
        sketch_op.sync_sketch_data(FakeDrive(), "source", "target")
    finally:
        sketch_op.create_engine = original_engine
        sketch_op.read_secret = original_secret

    with Session(engine) as session:
        row = session.execute(select(Sketch)).scalar_one()
        assert row.name == "示例短剧"
        assert row.fid == "target-fid"


def test_longest_common_substring_basic():
    from funsketch.sketch.task.load import longest_common_substring

    assert (
        longest_common_substring(["xxabcdefxx", "yyabcdefyy", "abcdefzz"]) == "abcdef"
    )


def test_longest_common_substring_empty_list():
    from funsketch.sketch.task.load import longest_common_substring

    assert longest_common_substring([]) == ""


def test_longest_common_substring_single_string():
    from funsketch.sketch.task.load import longest_common_substring

    assert longest_common_substring(["hello"]) == "hello"


def test_longest_common_substring_no_overlap():
    from funsketch.sketch.task.load import longest_common_substring

    assert longest_common_substring(["abc", "xyz"]) == ""


def test_sketch_get_uid_and_to_dict_is_pure():
    """SQLAlchemy 声明模型无需数据库会话即可构造和计算标识。"""
    from funsketch.db import Sketch

    sketch = Sketch(name="替嫁侯府", fid="fid-1", video_fid="video-fid-1")

    assert sketch._get_uid() == "替嫁侯府"
    expected_uid = hashlib.md5("替嫁侯府".encode("utf-8")).hexdigest()
    assert sketch.get_uid() == expected_uid
    assert sketch.to_dict() == {
        "name": "替嫁侯府",
        "fid": "fid-1",
        "video_fid": "video-fid-1",
        "uid": expected_uid,
    }


def test_episode_get_uid_and_to_dict_is_pure():
    from funsketch.db import Episode

    episode = Episode(sketch_id="sketch-1", index=3, name="ep3", size=100, fid="fid-3")

    assert episode._get_uid() == "sketch-1:3"
    expected_uid = hashlib.md5("sketch-1:3".encode("utf-8")).hexdigest()
    assert episode.get_uid() == expected_uid
    assert episode.to_dict()["uid"] == expected_uid


def test_analyse_get_uid_and_to_dict_is_pure():
    from funsketch.db.analyse import Analyse

    analyse = Analyse(
        sketch_id="sketch-1",
        episode_id="ep-1",
        folder="text",
        name="ep1.txt",
        size=42,
        fid="fid-x",
        text="hello world",
    )

    assert analyse._get_uid() == "ep-1:text"
    expected_uid = hashlib.md5("ep-1:text".encode("utf-8")).hexdigest()
    assert analyse.get_uid() == expected_uid
    assert analyse.to_dict()["uid"] == expected_uid


def test_base_task_success_lifecycle(tmp_path):
    """BaseTask 只通过本地临时文件记录成功状态。"""
    from funsketch.sketch.task.base import BaseTask

    class DummySketch:
        pass

    task = BaseTask(sketch=DummySketch())
    task.success_file = str(tmp_path / "SUCCESS")

    assert task.is_success() is False

    calls = []
    task._run = lambda *a, **k: calls.append(1)
    task.run()

    assert calls == [1]
    assert task.is_success() is True

    # 未要求重试时，第二次运行应直接跳过。
    task.run()
    assert calls == [1]

    # 要求重试时，应删除成功标记并重新运行。
    task.run(retry=True)
    assert calls == [1, 1]


def test_task_run_delegates_to_all_children():
    from funsketch.sketch.task.base import BaseTask, TaskRun

    class DummySketch:
        pass

    calls = []

    class RecordingTask(BaseTask):
        def __init__(self, name):
            super().__init__(sketch=DummySketch())
            self.name = name

        def run(self, *args, **kwargs):
            calls.append(self.name)

    task_run = TaskRun(
        task_list=[RecordingTask("a"), RecordingTask("b")],
        sketch=DummySketch(),
    )
    task_run.run()

    assert calls == ["a", "b"]


# 命令行入口测试


def test_no_cli_entry_point_declared():
    """项目当前未声明命令行入口。"""
    import pathlib

    pyproject = (
        pathlib.Path(__file__).resolve().parent.parent / "pyproject.toml"
    )
    content = pyproject.read_text(encoding="utf-8")
    assert "[project.scripts]" not in content


# 使用本地替身覆盖依赖外部系统的业务路径。


def test_get_default_drive_logs_in_both_drives(monkeypatch):
    from funsketch.op import drive as drive_op

    calls = []

    class FakeDrive:
        def login(self, **kwargs):
            calls.append(kwargs)

    monkeypatch.setattr(drive_op, "AlipanDrive", FakeDrive)
    monkeypatch.setattr(drive_op, "AliopenDrive", FakeDrive)
    first, second = drive_op.get_default_drive()

    assert isinstance(first, FakeDrive)
    assert isinstance(second, FakeDrive)
    assert calls == [{}, {}]


def test_sync_episode_data_with_fake_dependencies(monkeypatch):
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import Session

    from funsketch.db import Episode, Sketch
    from funsketch.op import episode as episode_op

    engine = create_engine("sqlite:///:memory:")

    class FakeDrive:
        def get_file_list(self, _fid):
            return [{"fid": "video-1", "name": "第一集.mp4"}]

    class FakeModel:
        def chat(self, _prompt):
            return '[{"path":"video-1","index":1,"name":"第一集"}]'

    episode_op.BaseTable.metadata.create_all(engine)
    with Session(engine) as session:
        Sketch(name="短剧", fid="target", video_fid="source").upsert(session=session)
        session.commit()

    monkeypatch.setattr(episode_op, "create_engine", lambda *_a, **_k: engine)
    monkeypatch.setattr(episode_op, "read_secret", lambda *_a: "unused")
    monkeypatch.setattr(episode_op, "get_default_drive", lambda: (FakeDrive(), None))
    monkeypatch.setattr(episode_op, "get_model", lambda _name: FakeModel())
    episode_op.sync_episode_data()

    with Session(engine) as session:
        row = session.execute(select(Episode)).scalar_one()
        assert row.name == "第一集"
        assert row.index == 1


def test_sync_episode_data_reports_invalid_model_response(monkeypatch):
    """模型返回非 JSON 时，应包含短剧标识和原始异常。"""
    from funsketch.op.episode import _parse_episode_response

    try:
        _parse_episode_response("not-json", "sketch-1")
    except ValueError as exc:
        assert "sketch-1" in str(exc)
        assert isinstance(exc.__cause__, json.JSONDecodeError)
    else:
        raise AssertionError("非法模型响应应抛出 ValueError")


def test_update_text_episode_handles_empty_database(monkeypatch):
    from sqlalchemy import create_engine

    from funsketch.op import analyse as analyse_op

    engine = create_engine("sqlite:///:memory:")
    monkeypatch.setattr(analyse_op, "create_engine", lambda *_a, **_k: engine)
    monkeypatch.setattr(analyse_op, "read_secret", lambda *_a: "unused")
    monkeypatch.setattr(analyse_op, "get_default_drive", lambda: (object(), object()))

    analyse_op.update_text_episode()


def test_update_text_episode_processes_and_overwrites_existing_text(monkeypatch):
    """文本同步应入库，已有文本跳过，overwrite 时重新处理。"""
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import Session

    from funsketch.db import Episode, Sketch
    from funsketch.db.analyse import Analyse
    from funsketch.op import analyse as analyse_op

    engine = create_engine("sqlite:///:memory:")
    analyse_op.BaseTable.metadata.create_all(engine)
    with Session(engine) as session:
        sketch = Sketch(name="短剧", fid="sketch-dir", video_fid="video-dir")
        sketch.upsert(session=session)
        episode = Episode(
            sketch_id=sketch.uid, index=1, name="第一集", fid="video-1"
        )
        episode_id = episode.uid
        episode.upsert(session=session)
        session.commit()

    processed = []

    class FakeEpisodePath:
        def __init__(self, episode):
            self.episode = episode
            self.text_path = f"{episode.uid}.txt"

        def download_video(self, driver):
            processed.append(("download", self.episode.uid))

        def convert_video(self):
            processed.append(("convert", self.episode.uid))

        def detect_text(self):
            processed.append(("text", self.episode.uid))

    class UploadDrive:
        def __init__(self):
            self.files = []

        def mkdir(self, fid, name):
            assert fid == "sketch-dir"
            assert name == "text"
            return "text-dir"

        def upload_file(self, filedir, fid):
            assert fid == "text-dir"
            self.files.append(
                SimpleNamespace(name=filedir, fid=f"fid-{len(self.files) + 1}-{filedir}")
            )

        def get_file_list(self, fid):
            assert fid == "text-dir"
            return self.files

    upload_drive = UploadDrive()
    monkeypatch.setattr(analyse_op, "create_engine", lambda *_a, **_k: engine)
    monkeypatch.setattr(analyse_op, "read_secret", lambda *_a: "unused")
    monkeypatch.setattr(
        analyse_op, "get_default_drive", lambda: (upload_drive, object())
    )
    monkeypatch.setattr(analyse_op, "EpisodePath", FakeEpisodePath)

    analyse_op.update_text_episode()
    analyse_op.update_text_episode()
    analyse_op.update_text_episode(overwrite=True)

    assert processed == [
        ("download", episode_id),
        ("convert", episode_id),
        ("text", episode_id),
        ("download", episode_id),
        ("convert", episode_id),
        ("text", episode_id),
    ]
    with Session(engine) as session:
        row = session.execute(select(Analyse)).scalar_one()
        assert row.episode_id == episode_id
        assert row.fid == f"fid-2-{episode_id}.txt"


def test_update_episode_processes_short_text(monkeypatch):
    """短文本分集会完成下载、转写、上传并回写文本路径。"""
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import Session

    from funsketch.db import Episode
    from funsketch.episode import update as update_op

    engine = create_engine("sqlite:///:memory:")
    update_op.Episode.metadata.create_all(engine)
    with Session(engine) as session:
        episode = Episode(
            sketch_id="sketch-1", index=1, name="第一集", fid="video-1", text=""
        )
        episode.upsert(session=session)
        session.commit()

    steps = []

    class FakeEpisodePath:
        def __init__(self, episode):
            self.episode = episode
            self.text_path = "text/episode-1.txt"

        def download_video(self, driver):
            steps.append("download")

        def convert_video(self):
            steps.append("convert")

        def detect_text(self):
            steps.append("text")

    class FakeDrive:
        def __init__(self):
            self.uploads = []

        def upload_file(self, local_path, fid):
            self.uploads.append((local_path, fid))

    drive = FakeDrive()
    monkeypatch.setattr(update_op, "EpisodePath", FakeEpisodePath)
    update_op.update_episode(engine=engine, drive=drive)

    assert steps == ["download", "convert", "text"]
    assert drive.uploads == [("text/episode-1.txt", "/text/episode-1.txt")]
    with Session(engine) as session:
        row = session.execute(select(Episode)).scalar_one()
        assert row.text == "/text/episode-1.txt"


def test_load_task_uses_supplied_credentials(monkeypatch, tmp_path):
    from funsketch.sketch.meta import SketchMeta
    from funsketch.sketch.task import load as load_task

    calls = []

    class FakeDrive:
        def login(self, **kwargs):
            calls.append(kwargs)

    monkeypatch.setattr(load_task, "BaiDuDrive", FakeDrive)
    sketch = SketchMeta("url", "pwd", "demo", str(tmp_path))
    task = load_task.LoadTask(
        bduss="b", stoken="s", ptoken="p", sketch=sketch
    )

    assert isinstance(task.drive, FakeDrive)
    assert calls == [{"bduss": "b", "stoken": "s", "ptoken": "p"}]


def test_audio_task_extracts_mp4(monkeypatch, tmp_path):
    from funsketch.sketch.meta import SketchMeta
    from funsketch.sketch.task import audio as audio_task

    sketch = SketchMeta("url", "pwd", "demo", str(tmp_path))
    os.makedirs(sketch.result_video)
    (tmp_path / "demo" / "result" / "video" / "001.mp4").touch()
    writes = []

    class FakeAudio:
        def write_audiofile(self, path):
            writes.append(path)

        def close(self):
            pass

    class FakeVideo:
        audio = FakeAudio()

        def __init__(self, _path):
            pass

        def close(self):
            pass

    monkeypatch.setattr(audio_task, "VideoFileClip", FakeVideo)
    audio_task.AudioTask(sketch=sketch)._run()

    assert writes == [os.path.join(sketch.result_audio, "001.wav")]


def test_text_task_transcribes_wav(monkeypatch, tmp_path):
    from funsketch.sketch.meta import SketchMeta
    from funsketch.sketch.task import text as text_task

    sketch = SketchMeta("url", "pwd", "demo", str(tmp_path))
    os.makedirs(sketch.result_audio)
    (tmp_path / "demo" / "result" / "audio" / "001.wav").touch()

    class FakeModel:
        def __init__(self, name):
            assert name == "turbo"

        def transcribe(self, path, language):
            assert path.endswith("001.wav")
            assert language == "zh"
            return {"text": "内容"}

    monkeypatch.setattr(text_task, "WhisperASR", FakeModel)
    text_task.TextTask(sketch=sketch)._run()

    text_path = tmp_path / "demo" / "result" / "text" / "001.txt"
    assert json.loads(text_path.read_text(encoding="utf-8")) == {"text": "内容"}


def test_episode_path_downloads_to_expected_path(monkeypatch, tmp_path):
    from funsketch.db import Episode
    from funsketch.episode.update import EpisodePath

    monkeypatch.chdir(tmp_path)
    episode = Episode(sketch_id="sketch", index=2, fid="video")
    calls = []

    class FakeDrive:
        def download_file(self, *args, **kwargs):
            calls.append((args, kwargs))

    path = EpisodePath(episode)
    path.download_video(FakeDrive())

    assert calls[0][0] == ("video",)
    assert calls[0][1]["filepath"].endswith(f"002-{episode.uid}.mp4")


def test_add_sketch_with_sqlite():
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import Session

    from funsketch.db import Sketch
    from funsketch.db.sketch import add_sketch

    engine = create_engine("sqlite:///:memory:")
    add_sketch(engine, "短剧", "target", "source")

    with Session(engine) as session:
        row = session.execute(select(Sketch)).scalar_one()
        assert row.name == "短剧"
        assert row.fid == "target"

"""Lightweight smoke tests for funsketch.

funsketch is a personal short-drama/video pipeline that needs real
`funsecret` credentials plus live cloud-drive (alipan/baidu/webdav) and
video/ASR (moviepy + funtalk WhisperASR) access for almost everything it
does. There is no way to exercise the real business flows in a sandboxed
CI-like environment without those credentials, so this suite:

  * imports every module that *can* be imported without touching real
    credentials/network, and asserts that succeeds;
  * exercises the small number of genuinely pure-logic helpers (path
    building, uid hashing, longest-common-substring, local-file based
    task bookkeeping) with real inputs;
  * explicitly skips (never fakes) anything that needs a live DB engine,
    a logged-in cloud drive, or a real ASR/LLM model.

Known upstream bug worked around here (documented, not fixed):
`funget.download.multi` (pulled in transitively via
`fundrive.drives.baidu`) does `from funfile.compress.utils import
file_tqdm_bar`, but the currently published `funfile` (1.0.39) only
exposes `file_tqdm_bar` from `funfile.compress` itself -- the `.utils`
submodule does not exist. This breaks importing
`funsketch.sketch.task` (and anything that transitively imports
`fundrive.drives.baidu`) in a clean environment. We register a tiny
shim module in `sys.modules` so the import chain resolves purely for
test purposes; the actual bug lives in `funget`/`funfile`, not in
funsketch, and is out of scope for this smoke-test PR.
"""

import hashlib
import os
import sys
import types

import pytest

# --- Workaround for the funget/funfile upstream bug described above ---
try:
    import funfile.compress as _funfile_compress

    if "funfile.compress.utils" not in sys.modules:
        _shim = types.ModuleType("funfile.compress.utils")
        _shim.file_tqdm_bar = _funfile_compress.file_tqdm_bar
        sys.modules["funfile.compress.utils"] = _shim
except ImportError:
    pass


def test_import_top_level_package():
    """The top-level package must import without side effects."""
    import funsketch  # noqa: F401


def test_import_db_module():
    """funsketch.db has no credential/network needs at import time."""
    import funsketch.db as db

    assert db.__all__ == ["Sketch", "Episode", "Analyse"]


def test_import_op_module():
    """funsketch.op only touches credentials when functions are *called*."""
    import funsketch.op as op

    assert set(op.__all__) == {
        "sync_sketch_data",
        "sync_episode_data",
        "update_text_episode",
    }


def test_import_episode_update_module():
    import funsketch.episode.update  # noqa: F401


def test_import_sketch_task_module():
    """Only importable thanks to the funget/funfile shim above."""
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


# ---------------------------------------------------------------------
# Pure-logic tests
# ---------------------------------------------------------------------


def test_sketch_meta_paths_are_pure_string_building():
    """SketchMeta.__init__ only builds path strings, no I/O."""
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
    """SQLAlchemy declarative models can be built/hashed with no DB/session."""
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
    """BaseTask's success-file bookkeeping only touches a local tmp file."""
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

    # Second run without retry should skip _run entirely.
    task.run()
    assert calls == [1]

    # With retry=True it removes the success file and runs again.
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


# ---------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------


def test_no_cli_entry_point_declared():
    """funsketch's pyproject.toml has no [project.scripts] section.

    There is no CLI entry point to smoke-test with --help; this test
    just documents that fact so a future CLI addition doesn't silently
    go untested.
    """
    import pathlib

    pyproject = (
        pathlib.Path(__file__).resolve().parent.parent / "pyproject.toml"
    )
    content = pyproject.read_text(encoding="utf-8")
    assert "[project.scripts]" not in content


# ---------------------------------------------------------------------
# Things that need real credentials / cloud APIs / heavy models: skipped
# honestly rather than faked.
# ---------------------------------------------------------------------


def test_get_default_drive_needs_real_credentials():
    pytest.skip(
        "funsketch.op.drive.get_default_drive() logs into real Alipan/BaiDu "
        "accounts via funsecret credentials and live network calls; "
        "需要真实凭据，跳过"
    )


def test_sync_sketch_data_needs_real_credentials():
    pytest.skip(
        "funsketch.op.sketch.sync_sketch_data() needs a real DB URL via "
        "funsecret and a logged-in cloud drive; 需要真实凭据，跳过"
    )


def test_sync_episode_data_needs_real_credentials():
    pytest.skip(
        "funsketch.op.episode.sync_episode_data() needs a real DB, a "
        "logged-in cloud drive, and a live deepseek LLM call; "
        "需要真实凭据，跳过"
    )


def test_update_text_episode_needs_real_credentials():
    pytest.skip(
        "funsketch.op.analyse.update_text_episode() needs a real DB, a "
        "logged-in cloud drive, moviepy video files, and the funtalk "
        "WhisperASR model; 需要真实凭据，跳过"
    )


def test_load_task_needs_real_baidu_credentials():
    pytest.skip(
        "LoadTask.__init__ logs into a real BaiDu Drive account using "
        "funsecret-cached bduss/stoken/ptoken; 需要真实凭据，跳过"
    )


def test_audio_task_needs_real_video_files_and_moviepy():
    pytest.skip(
        "AudioTask._run() needs real downloaded .mp4 files and moviepy's "
        "ffmpeg backend to extract audio; 需要真实媒体文件与外部依赖，跳过"
    )


def test_text_task_needs_real_asr_model():
    pytest.skip(
        "TextTask.__init__ loads funtalk's WhisperASR('turbo') model and "
        "TextTask._run() transcribes real audio; 需要真实模型/音频，跳过"
    )


def test_episode_path_needs_real_asr_and_video_tools():
    pytest.skip(
        "EpisodePath (funsketch.episode.update / funsketch.op.analyse) "
        "downloads real video via a cloud drive, extracts audio with "
        "moviepy, and transcribes with funtalk WhisperASR; 需要真实凭据与"
        "外部依赖，跳过"
    )


def test_add_sketch_needs_real_db_engine():
    pytest.skip(
        "funsketch.db.sketch.add_sketch() needs a real SQLAlchemy Engine "
        "pointed at a live database; 需要真实数据库，跳过"
    )

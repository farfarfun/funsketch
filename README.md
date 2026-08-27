# funsketch

短剧（sketch）资源的下载与自动化预处理流水线：从网盘分享链接批量下载某部短剧的全部视频，用 [moviepy](https://github.com/Zulko/moviepy) 提取音频，用 `funtalk` 的 `WhisperASR` 把音频转成文字，再用 `funai` 里配置的 LLM（默认 deepseek）根据文件名推断分集顺序，全部元数据（剧集、分集、转写结果）通过 `fundb`/SQLAlchemy 存进数据库。

这是作者的个人自动化工具，运行依赖大量私有配置（阿里云盘/百度网盘/WebDav 账号、数据库连接串等，均通过 [funsecret](https://github.com/farfarfun/funsecret) 读取），不经过额外配置无法直接跑起来。

## 安装

```bash
pip install funsketch
```

## 核心概念

- `funsketch.sketch.meta.SketchMeta`：一部短剧的元信息（网盘分享链接、提取码、名称、本地缓存目录）。
- `funsketch.sketch.task`：按 `SketchMeta` 执行流水线任务，每个任务都基于 `BaseTask`（支持通过 `SUCCESS` 标记文件跳过已完成的步骤）：
  - `LoadTask`：用 `fundrive` 的百度网盘驱动保存分享链接、下载全部视频到本地；
  - `AudioTask`：用 `moviepy` 把下载好的视频批量转成 `.wav` 音频；
  - `TextTask`：用 `funtalk.asr.WhisperASR("turbo")` 把音频转写成文字。
- `funsketch.db`：`Sketch`（剧集）、`Episode`（分集）、`Analyse`（转写等分析结果）三张表，基于 `fundb.sqlalchemy.table.BaseTable`。
- `funsketch.op`：另一套面向网盘目录同步的操作集合（`sync_sketch_data`、`sync_episode_data`、`update_text_episode` 等），用 `fundrive`（阿里云盘）而非 `LoadTask` 使用的百度网盘驱动。

## 用法示例

```python
from funsketch.sketch.meta import SketchMeta
from funsketch.sketch.task.load import LoadTask
from funsketch.sketch.task.audio import AudioTask
from funsketch.sketch.task.text import TextTask

sketch = SketchMeta(shared_url="https://pan.baidu.com/s/xxxx", pwd="xxxx", name="示例短剧")

LoadTask(sketch=sketch).run()   # 下载分享链接里的全部 mp4
AudioTask(sketch=sketch).run()  # 提取音频
TextTask(sketch=sketch).run()   # Whisper 转写文字
```

需要先通过 `funsecret` 配置好网盘登录凭证（如 `fundrive`/`baidu`/`bduss`、`stoken`、`ptoken`）和数据库连接串（`funsketch`/`db`/`url`）。

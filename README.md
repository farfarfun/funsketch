# funsketch

短剧（sketch）资源的下载与自动化预处理流水线：从网盘分享链接批量下载某部短剧的全部视频，用 [moviepy](https://github.com/Zulko/moviepy) 提取音频，用 `funtalk` 的 `WhisperASR` 把音频转成文字，再用 `funai` 里配置的 LLM（默认 deepseek）根据文件名推断分集顺序，全部元数据（剧集、分集、转写结果）通过 `fardb`/SQLAlchemy 存进数据库。

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
- `funsketch.db`：`Sketch`（剧集）、`Episode`（分集）、`Analyse`（转写等分析结果）三张表，基于 `fardb.sqlalchemy.table.BaseTable`。
- `funsketch.op`：另一套面向网盘目录同步的操作集合（`sync_sketch_data`、`sync_episode_data`、`update_text_episode` 等），用 `fundrive`（阿里云盘）而非 `LoadTask` 使用的百度网盘驱动。

## 用法示例

运行流水线前，需要安装 FFmpeg（供 moviepy 使用）、可用的 Whisper 模型环境，以及可访问的百度网盘分享资源。先用 `funsecret` 写入百度网盘登录凭证（替换成你自己账号的真实值）：

```python
from funsecret import write_secret

write_secret("你的bduss", "fundrive", "baidu", "bduss")
write_secret("你的stoken", "fundrive", "baidu", "stoken")
write_secret("你的ptoken", "fundrive", "baidu", "ptoken")
```

`funsketch.op` 的同步流程还需要阿里云盘凭据，以及数据库连接串。数据库配置示例如下（SQLite 适合本地试运行）：

```python
from funsecret import write_secret

write_secret("sqlite:///funsketch.db", "funsketch", "db", "url")
```

然后把下面示例里的 `shared_url`/`pwd` 换成你要下载的短剧分享链接和提取码即可运行：

```python
from funsketch.sketch.meta import SketchMeta
from funsketch.sketch.task.load import LoadTask
from funsketch.sketch.task.audio import AudioTask
from funsketch.sketch.task.text import TextTask

# shared_url/pwd 替换为真实的网盘分享链接与提取码
sketch = SketchMeta(shared_url="https://pan.baidu.com/s/xxxx", pwd="xxxx", name="示例短剧")

LoadTask(sketch=sketch).run()   # 下载分享链接里的全部 mp4
AudioTask(sketch=sketch).run()  # 提取音频
TextTask(sketch=sketch).run()   # Whisper 转写文字
```

这是一条依赖真实网盘账号和分享资源的流水线，无法在不接入外部网盘的情况下提供完全离线的示例。配置 `funsketch.op` 所需的阿里云盘凭据和数据库连接串后，可编辑 `example/step1.py` 中的目录 ID 与短剧名称，再执行：

```bash
python example/step1.py
```

---

## 关于 farfarfun

[farfarfun](https://github.com/farfarfun) 是一个专注于实用工具库的开源组织，
涵盖云存储、数据处理、AI、多媒体与开发工具链等方向。

- 🏠 组织主页：<https://github.com/farfarfun>
- 📦 PyPI：<https://pypi.org/user/niuliangtao/>
- 📧 联系：farfarfun@qq.com

本项目基于 [MIT](LICENSE) 协议开源。

# 更新日志

## 未发布

### 修复

- 移除 `get_default_drive()` 上无参数的全局认证缓存，避免不同凭据/过期会话被长期错误复用。
- `farlog` 依赖下限提升到 `>=1.1.7`，与组织规范一致。
- 为模型响应和网盘文本目录读写补充短剧、分集和文件定位上下文。
- 修复分集文本字段未映射及既有分集、分析记录未回写的问题。

### 变更

- 为 `episode/update.py`、`op/analyse.py` 的 `EpisodePath`/`update_episode`/`update_text_episode`、`sketch/task/base.py` 的 `BaseTask`/`TaskRun` 及 `db` 的 ORM 实体补齐类型标注和中文 docstring。

## 1.0.63

### 修复

- 统一日志和缓存入口，补齐直接依赖与可复现锁文件。
- 移除业务同步中的诊断 `print` 输出。

### 变更

- 补充公开同步 API 的类型标注和中文文档。

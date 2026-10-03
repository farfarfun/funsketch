import os
from typing import Any

from farlog import getLogger

from funsketch.sketch.meta import SketchMeta

logger = getLogger("funsketch")


class BaseTask:
    """可重试并通过 SUCCESS 文件记录完成状态的任务。"""

    def __init__(self, sketch: SketchMeta, *args: Any, **kwargs: Any) -> None:
        """绑定任务所属的短剧元数据；具体的成功标记路径由子类设置。"""
        self.sketch = sketch
        self.success_file: str | None = None

    def success(self) -> None:
        """在成功标记路径写入空文件，标记任务已完成。"""
        if self.success_file is not None:
            open(self.success_file, "a").close()

    def is_success(self) -> bool:
        """判断成功标记文件是否已存在。"""
        return self.success_file is not None and os.path.exists(self.success_file)

    def _run(self, *args: Any, **kwargs: Any) -> None:
        """子类实现的具体任务逻辑，默认不执行任何操作。"""

    def run(self, retry: bool = False, *args: Any, **kwargs: Any) -> None:
        """已成功且不要求重试时直接跳过，否则执行任务并写入成功标记。"""
        if self.is_success():
            if not retry:
                logger.success(
                    f"task already success, {self.success_file} exists, skipping."
                )
                return
            os.remove(self.success_file)
        self._run(*args, **kwargs)
        self.success()


class TaskRun(BaseTask):
    """按顺序运行一组子任务的组合任务。"""

    def __init__(self, task_list: list[BaseTask], *args: Any, **kwargs: Any) -> None:
        """保存待执行的子任务列表，并完成基类初始化。"""
        self.task_list = task_list
        super().__init__(*args, **kwargs)

    def run(self, *args: Any, **kwargs: Any) -> None:
        """依次调用每个子任务的 run 方法。"""
        for task in self.task_list:
            task.run(*args, **kwargs)

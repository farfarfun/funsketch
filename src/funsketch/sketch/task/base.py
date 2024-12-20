import os
from typing import List

from funutil import getLogger

from funsketch.sketch.meta import SketchMeta

logger = getLogger("funsketch")


class BaseTask:
    def __init__(self, sketch: SketchMeta, *args, **kwargs):
        self.sketch = sketch
        self.success_file = None

    def success(self):
        if self.success_file is not None:
            open(self.success_file, "a").close()

    def is_success(self):
        return self.success_file is not None and os.path.exists(self.success_file)

    def _run(self, *args, **kwargs):
        pass

    def run(self, retry=False, *args, **kwargs):
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
    def __init__(self, task_list: List[BaseTask], *args, **kwargs):
        self.task_list = task_list
        super().__init__(*args, **kwargs)

    def run(self, *args, **kwargs):
        for task in self.task_list:
            task.run(*args, **kwargs)

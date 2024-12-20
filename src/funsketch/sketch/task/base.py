from funsketch.sketch.meta import SketchMeta
from typing import List


class BaseTask:
    def __init__(self, *args, **kwargs):
        pass

    def run(self, sketch: SketchMeta, *args, **kwargs):
        pass


class TaskRun(BaseTask):
    def __init__(self, task_list: List[BaseTask], *args, **kwargs):
        self.task_list = task_list
        super().__init__(*args, **kwargs)

    def run(self, sketch: SketchMeta, *args, **kwargs):
        for task in self.task_list:
            task.run(sketch, *args, **kwargs)

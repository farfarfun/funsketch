from funsketch.sketch.meta import SketchMeta


class BaseTask:
    def __init__(self, *args, **kwargs):
        pass

    def run(self, sketch: SketchMeta, *args, **kwargs):
        pass

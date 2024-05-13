from .Mire import Mire


class ScaleBar:

    def __init__(self, start: Mire, end: Mire, length: float):
        self.start = start
        self.end = end
        self.length = length

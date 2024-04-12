from .File import File


class PointCloud(File):

    def __init__(self, path: str):
        super().__init__(path)

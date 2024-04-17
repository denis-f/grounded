from .File import File


class Raster(File):

    def __init__(self, path: str):
        super().__init__(path)

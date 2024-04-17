from .File import File


class Raster(File):

    def __init__(self, path: str):
        """
        Constructeur d'un object Mire3D

        Parameters :
            path (str) : chemin menant au fichier du raster
        """
        super().__init__(path)

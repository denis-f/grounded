from .File import File


class Raster(File):

    def __init__(self, path: str):
        """
        Constructeur d'un objet Raster.

        Args:
            path (str): Le chemin menant au fichier du raster.
        """
        super().__init__(path)

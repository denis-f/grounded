from .File import File


class PointCloud(File):

    def __init__(self, path: str):
        """
        Constructeur d'un objet PointCloud.

        Args:
            path (str): Le chemin menant au fichier du nuage de points.
        """
        super().__init__(path)

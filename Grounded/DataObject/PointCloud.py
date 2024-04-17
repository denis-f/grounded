from .File import File


class PointCloud(File):

    def __init__(self, path: str):
        """
        Constructeur d'un object PointCloud

        Parameters :
            path (str) = chemin menant au fichier du nuage de points
        """
        super().__init__(path)

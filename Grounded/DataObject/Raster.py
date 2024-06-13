from .File import File

import rasterio


class Raster(File):

    def __init__(self, path: str):
        """
        Constructeur d'un objet Raster.

        Args:
            path (str): Le chemin menant au fichier du raster.
        """
        super().__init__(path)
        with rasterio.open(path) as data_set:
            self.resolution = data_set.res[0]
            self.xy_function = data_set.xy
            self.transform = data_set.transform

    def xy(self, x, y) -> (float, float):
        return self.xy_function(x, y)

    def xy_3d_space_to_xy_raster(self, x: float, y: float) -> (float, float):
        """
        Convertis les coordonnées spatiales (x, y) en indices de pixel (row, col)
        Args:
            x (float): Coordonnées x dans l'espace 3D duquel est issu le raster
            y (float): Coordonnées y dans l'espace 3D duquel est issu le raster

        Returns: les coordonnées équivalentes x y (row, col) dans le raster
        """
        return ~self.transform * (x, y)

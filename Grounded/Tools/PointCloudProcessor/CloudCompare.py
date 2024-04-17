from .PointCloudProcessor import PointCloudProcessor
from Grounded.DataObject import File, PointCloud, Raster

import subprocess
import os


def deplacer_premier_fichier_avec_pattern(source_directory: str, destination_directory: str, pattern: str):
    files = os.listdir(source_directory)
    for file_name in files:
        if pattern in file_name:
            try:
                os.rename(os.path.join(source_directory, file_name), os.path.join(destination_directory, file_name))
                return PointCloud(os.path.join(destination_directory, file_name))
            except FileNotFoundError:
                raise Exception("Fichier introuvable")


def recuperer_premier_fichier_avec_pattern(directory: str, pattern: str):
    files = os.listdir(directory)
    for file_name in files:
        if pattern in file_name:
            try:
                return os.path.join(directory, file_name)
            except FileNotFoundError:
                raise Exception("Fichier introuvable")


class CloudCompare(PointCloudProcessor):
    """
    Cette classe implémente l'interface PointCloudProcessor et fournit des méthodes pour traiter les nuages de points
    à l'aide de l'outil CloudCompare.
    """

    def __init__(self):
        """
        Constructeur de la classe CloudCompare.
        """
        self.working_directory = os.path.abspath(os.path.join(os.curdir, "cloudCompare_working_directory"))
        os.makedirs(self.working_directory, exist_ok=True)

    def mise_a_echelle(self, point_cloud: PointCloud, facteur: float) -> PointCloud:
        """
        Méthode abstraite pour effectuer une mise à l'échelle d'un nuage de points.

        Arguments:
            point_cloud (PointCloud): Le nuage de points à mettre à l'échelle.
            facteur (float): Le facteur d'échelle à appliquer.

        Returns:
            PointCloud: Le nuage de points mis à l'échelle.
        """
        nom_matrice = os.path.join(self.working_directory, "scale_factor_matrix.txt")

        # création de la matrice qui va permettre la transformation
        with open(nom_matrice, 'w') as file:
            file.write(f"{facteur} 0 0 0\n"
                       f"0 {facteur} 0 0\n"
                       f"0 0 {facteur} 0\n"
                       f"0 0 0 1")

        # transformation du nuage de point
        subprocess.run(["cloudcompare.CloudCompare", "-SILENT", "-C_EXPORT_FMT", f"{point_cloud.extension.upper()}",
                        "-O", f"{point_cloud.path}", "-APPLY_TRANS", nom_matrice])

        # déplacement du nuage de point nouvellement généré se trouvant dans le dossier du nuage de points
        # donné en paramètre
        transformed_point_cloud = deplacer_premier_fichier_avec_pattern(point_cloud.get_path_directory(),
                                                                        self.working_directory, "TRANSFORMED")

        # suppression de la matrice
        try:
            os.remove(nom_matrice)
        except FileNotFoundError:
            raise Exception("Fichier introuvable")

        # on retourne le nouveau nuage de point
        return transformed_point_cloud

    def cloud_to_cloud_difference(self, point_cloud_before_excavation: PointCloud,
                                  point_cloud_after_excavation: PointCloud) -> Raster:
        """
        Méthode pour calculer la distance entre deux nuages de points.

        Arguments:
            point_cloud_before_excavation (PointCloud): Le nuage de points avant l'excavation.
            point_cloud_after_excavation (PointCloud): Le nuage de points après l'excavation.

        Returns:
            Raster: Un objet Raster correspondant à un fichier raster représentant la distance
            entre les deux nuages de points.
        """
        subprocess.run(["cloudcompare.CloudCompare", "-SILENT",
                        "-O", "-GLOBAL_SHIFT", "0", "0", "0", point_cloud_before_excavation.path,
                        "-O", "-GLOBAL_SHIFT", "0", "0", "0", point_cloud_after_excavation.path,
                        "-c2c_dist", "-MAX_DIST", "0.1",
                        "-AUTO_SAVE", "OFF",
                        "-RASTERIZE", "-GRID_STEP", "0.001", "-EMPTY_FILL", "INTERP", "-OUTPUT_RASTER_Z"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        postfix = "_C2C_DIST_MAX_DIST_0.1_RASTER_Z_"
        raster_before = Raster(recuperer_premier_fichier_avec_pattern(self.working_directory,
                                                                      point_cloud_before_excavation.get_name_without_extension()
                                                                      + postfix
                                                                      ))

        return raster_before

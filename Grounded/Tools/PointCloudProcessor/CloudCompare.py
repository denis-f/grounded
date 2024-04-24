from .PointCloudProcessor import PointCloudProcessor
from Grounded.DataObject import File, PointCloud, Raster
from Grounded.utils import find_files_regex, rename_file

import subprocess
import os
import shutil


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


def compare_versions(version1, version2):
    """
    Compare deux versions de logiciel.

    Args:
    version1 (str): La première version à comparer.
    version2 (str): La deuxième version à comparer.

    Returns:
    int: 0 si les deux versions sont égales, -1 si version1 est antérieure à version2, 1 si version1 est postérieure à version2.
    """
    v1 = version1.split('.')
    v2 = version2.split('.')

    for i in range(max(len(v1), len(v2))):
        num1 = int(v1[i]) if i < len(v1) else 0
        num2 = int(v2[i]) if i < len(v2) else 0

        if num1 < num2:
            return -1
        elif num1 > num2:
            return 1

    return 0


class CloudCompare(PointCloudProcessor):
    """
    Implémente l'interface PointCloudProcessor et fournit des méthodes pour traiter les nuages de points
    en utilisant l'outil CloudCompare.
    """

    def __init__(self, path_cloud_compare: str, version: str):
        """
        Constructeur de la classe CloudCompare.
        """
        self.working_directory = os.path.abspath(os.path.join(os.curdir, "cloudCompare_working_directory"))
        self.path_cloud_compare = path_cloud_compare
        self.set_up_working_space()
        self.is_v1_12_or_higher = compare_versions(version, '2.12') >= 0

    def set_up_working_space(self):
        if os.path.exists(self.working_directory):
            shutil.rmtree(self.working_directory)
        os.makedirs(self.working_directory, exist_ok=True)  # création du dossier de l'espace de travail cloud compare

    def mise_a_echelle(self, point_cloud: PointCloud, facteur: float) -> PointCloud:
        """
        Méthode abstraite pour effectuer une mise à l'échelle d'un nuage de points.

        Args:
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
        subprocess.run([self.path_cloud_compare, "-SILENT", "-NO_TIMESTAMP",
                        "-C_EXPORT_FMT", f"{point_cloud.extension.upper()}",
                        "-O", f"{point_cloud.path}", "-APPLY_TRANS", nom_matrice],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

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

    def cloud_to_cloud_distance(self, point_cloud_before_excavation: PointCloud,
                                point_cloud_after_excavation: PointCloud) -> Raster:
        """
        Méthode pour calculer la distance entre deux nuages de points.

        Args:
            point_cloud_before_excavation (PointCloud): Le nuage de points avant l'excavation.
            point_cloud_after_excavation (PointCloud): Le nuage de points après l'excavation.

        Returns:
            Raster: Un objet Raster correspondant à un fichier raster représentant la distance
            entre les deux nuages de points.
        """
        output_raster_option = "-OUTPUT_RASTER_Z"
        if self.is_v1_12_or_higher:
            output_raster_option += "_and_SF"

        subprocess.run([self.path_cloud_compare, "-SILENT", "-NO_TIMESTAMP",
                        "-O", "-GLOBAL_SHIFT", "0", "0", "0", point_cloud_before_excavation.path,
                        "-O", "-GLOBAL_SHIFT", "0", "0", "0", point_cloud_after_excavation.path,
                        "-c2c_dist", "-MAX_DIST", "0.1",
                        "-AUTO_SAVE", "OFF",
                        "-RASTERIZE", "-GRID_STEP", "0.001", "-EMPTY_FILL", "INTERP", output_raster_option],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        postfix = "_C2C_DIST_MAX_DIST_0.1_RASTER_Z"
        raster_before = Raster(find_files_regex(self.working_directory, point_cloud_before_excavation.get_name_without_extension() + postfix)[0])
        find_files_regex(self.working_directory, point_cloud_before_excavation.get_name_without_extension() + postfix)
        return raster_before

    def crop_point_cloud(self, point_cloud: PointCloud, coordonnees_trace: list[tuple[float, float]]) -> PointCloud:
        formated_coordinates = [str(coord) for point in coordonnees_trace for coord in point]
        command = ([self.path_cloud_compare, "-SILENT",
                    "-C_EXPORT_FMT", "ASC",
                    "-O", "-GLOBAL_SHIFT", "0", "0", "0", point_cloud.path,
                    "-CROP2D", "Z", str(len(coordonnees_trace))] + formated_coordinates +
                   ["-DELAUNAY", "-BEST_FIT",
                    "-SAMPLE_MESH", "DENSITY", "10000000"])

        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        path_point_cloud = find_files_regex(self.working_directory, f"{point_cloud.get_name_without_extension()}"
                                                                    "_CROPPED_SAMPLED_POINTS")[0]
        path_point_cloud = rename_file(path_point_cloud, f"{point_cloud.get_name_without_extension()}"
                                                         "_CROPPED")
        return PointCloud(path_point_cloud)

    def volume_between_clouds(self, crop_before: PointCloud, crop_after: PointCloud):
        subprocess.run([self.path_cloud_compare, "-SILENT",
                        "-O", "-GLOBAL_SHIFT", "0", "0", "0", crop_after.path,
                        "-O", "-GLOBAL_SHIFT", "0", "0", "0", crop_before.path,
                        "-VOLUME", "-GRID_STEP", "0.001"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        report_path = find_files_regex(self.working_directory, "VolumeCalculationReport")[0]
        with open(report_path, 'r') as file:
            content = file.read()

        volume = float(content.split("\n")[0].split()[1])
        os.remove(report_path)
        return volume

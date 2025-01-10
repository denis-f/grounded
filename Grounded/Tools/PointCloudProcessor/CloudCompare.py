from .PointCloudProcessor import PointCloudProcessor
from Grounded.DataObject import PointCloud, Raster
from Grounded.utils import (find_files_regex, rename_file, move_file_to_directory, config_builer,
                            check_module_executable_path)

import os
import re
import Grounded.logger as logger
import logging


class CloudCompare(PointCloudProcessor):
    """
    Implémente l'interface PointCloudProcessor et fournit des méthodes pour traiter les nuages de points
    en utilisant l'outil CloudCompare.
    """

    def __init__(self, path_cloud_compare: str, working_directory: str, output_dir: str):
        """
        Constructeur de la classe CloudCompare.
        """
        super().__init__(working_directory, output_dir)
        check_module_executable_path(path_cloud_compare, "CloudCompare")

        self.path_cloud_compare = path_cloud_compare
        self.set_up_working_space()
        self.is_v2_12_or_higher = self.check_version(path_cloud_compare)

    def check_version(self, path_cloud_compare):
        # on crée un appel de cloudCompare en logguant les sorties dans un fichier et en appellant l'option CSF, disponible seulement à partir de la 2.12
        # comme on fait exprès d'aller chercher (ou pas) une erreur dans un appel à CloudCompare, on met temporairement le niveau de débugage au mini
        log = logger.get_logger()
        saveLogLevel = log.level
        log.level = logging.INFO
        self.subprocess([path_cloud_compare,"-SILENT", "-LOG_FILE", "logCC.txt", "-CSF"],
                   os.path.join(self.working_directory, "DummyCCCall.log"))
        # Une fois l'appel CloudCompare réalisé on restaure le niveau de debug à l'initial
        log.level = saveLogLevel

        # On ouvre ensuite ce texte
        text_file = open("logCC.txt", "r")
        # a priori si pas d'erreur on est en version >=2.12
        is_v2_12_or_higher = True
        for line in text_file:
            # on cherche le pattern "Unknown"
            if re.search("Unknown", line):
                # et si c'est associé au pattern "CSF" c'est qu'on est en version 2.11 ou inférieure
                if re.search("CSF", line):
                    is_v2_12_or_higher = False
        # ici il faudrait supprimer le fichier logCC.txt
        os.remove("logCC.txt")
        return is_v2_12_or_higher

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
        self.subprocess([self.path_cloud_compare, "-SILENT", "-NO_TIMESTAMP",
                         "-C_EXPORT_FMT", f"{point_cloud.extension.upper()}",
                         "-O", f"{point_cloud.path}", "-APPLY_TRANS", nom_matrice],
                        os.path.join(self.working_directory, "Rescale.log"))

        # déplacement du nuage de point nouvellement généré se trouvant dans le dossier du nuage de points
        # donné en paramètre
        path_point_cloud = self.move_file_to_working_directory(point_cloud.get_path_directory(),
                                                               "TRANSFORMED", point_cloud.get_name_without_extension()) #TODO : ajouter un CC_rescaled au nom de base

        # suppression de la matrice
        try:
            os.remove(nom_matrice)
        except FileNotFoundError:
            raise Exception("Fichier introuvable")

        # on retourne le nouveau nuage de point
        return PointCloud(path_point_cloud)

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
        if self.is_v2_12_or_higher:
            output_raster_option += "_and_SF"

        self.subprocess([self.path_cloud_compare, "-SILENT", "-NO_TIMESTAMP",
                         "-O", "-GLOBAL_SHIFT", "0", "0", "0", point_cloud_before_excavation.path,
                         "-O", "-GLOBAL_SHIFT", "0", "0", "0", point_cloud_after_excavation.path,
                         "-c2c_dist", "-MAX_DIST", "0.1",
                         "-AUTO_SAVE", "OFF",
                         "-RASTERIZE", "-GRID_STEP", "0.001", "-EMPTY_FILL", "INTERP", output_raster_option],
                        os.path.join(self.working_directory, "Distance.log"))

        postfix = "_C2C_DIST_MAX_DIST_0.1_RASTER_Z"

        raster_path = self.move_file_to_working_directory(point_cloud_before_excavation.get_path_directory(),
                                                          f"{point_cloud_before_excavation.get_name_without_extension()}{postfix}",
                                                          f"{point_cloud_before_excavation.get_name_without_extension()}_CLOUD_TO_CLOUD_DISTANCE")

        return Raster(raster_path)

    def crop_point_cloud(self, point_cloud: PointCloud, coordonnees_trace: list[tuple[float, float]]) -> PointCloud:
        """
        Méthode permettant de découper un nuage de points à partir d'une liste de coordonnées délimitant
        les contours.

        Args:
            point_cloud (PointCloud): le nuage de point dans lequel effectuer la découpe
            coordonnees_trace (list): coordonnées détourant la zone de découpe

        Returns:
            PointCloud: nuage de points de la partie découpée

        """
        formated_coordinates = [str(coord) for point in coordonnees_trace for coord in point]
        command = ([self.path_cloud_compare, "-SILENT",
                    "-C_EXPORT_FMT", "ASC",
                    "-O", "-GLOBAL_SHIFT", "0", "0", "0", point_cloud.path,
                    "-CROP2D", "Z", str(len(coordonnees_trace))] + formated_coordinates +
                   ["-DELAUNAY", "-BEST_FIT",
                    "-SAMPLE_MESH", "DENSITY", "10000000"])

        self.subprocess(command, os.path.join(self.working_directory, "Crop.log"))

        path_cloud = self.move_file_to_working_directory(point_cloud.get_path_directory(),
                                                         f"{point_cloud.get_name_without_extension()}_CROPPED_SAMPLED_POINTS",
                                                         f"{point_cloud.get_name_without_extension()}_CROPPED")
        return PointCloud(path_cloud)

    def volume_between_clouds(self, crop_before: PointCloud, crop_after: PointCloud) -> float:
        """
        Méthode pour calculer le volume se trouvant entre deux nuages de points

        Args:
            crop_before (PointCloud): Le nuage de points découpé avant l'excavation.
            crop_after (PointCloud): Le nuage de points découpé après l'excavation.

        Returns:
            float: le volume calculé
        """
        arguments = [self.path_cloud_compare, "-SILENT",
                     "-O", "-GLOBAL_SHIFT", "0", "0", "0", crop_after.path,
                     "-O", "-GLOBAL_SHIFT", "0", "0", "0", crop_before.path,
                     "-VOLUME", "-GRID_STEP", "0.001"]
        self.subprocess(arguments, os.path.join(self.working_directory, "Volume.log"))

        # Lecture des résultats dans le fichier généré automatiquement
        report_path = find_files_regex(crop_before.get_path_directory(), "VolumeCalculationReport")[0]
        with open(report_path, 'r') as file:
            content = file.read()

        volume = float(content.split("\n")[0].split()[1])

        # Suppression du fichier contenant les résultats
        os.remove(report_path)

        return volume

    def move_file_to_working_directory(self, source_directory: str, regex: str, new_name: str):
        path_point_cloud = find_files_regex(source_directory, regex)[0]
        path_point_cloud = move_file_to_directory(path_point_cloud, self.working_directory)
        path_point_cloud = rename_file(path_point_cloud, new_name)
        return path_point_cloud

    def get_config(self) -> str:
        return config_builer(self, "CloudCompare")

from .PointCloudProcessor import PointCloudProcessor
from Grounded.DataObject import PointCloud
from Grounded.DataObject import File
from Grounded.DataObject import PointCloud

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


class CloudCompare(PointCloudProcessor):

    def __init__(self):
        self.working_directory = os.path.abspath(os.path.join(os.curdir, "cloudCompare_working_directory"))
        os.makedirs(self.working_directory, exist_ok=True)

    def mise_a_echelle(self, point_cloud: PointCloud, facteur: float) -> PointCloud:
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

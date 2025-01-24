import os
from exif import Image as exifImage
import numpy as np

import shutil

from Grounded.DataObject import Image
from Grounded.DataObject import Mire2D
from Grounded.DataObject import File
from .DetecteurMire import DetecteurMire

import subprocess

from Grounded.utils import config_builer, check_module_executable_path, path_exist, raise_logged
import Grounded.logger as logger


def parsing_result(resultat: str) -> list[Image]:
    """"
    Parse les sorties standard et d'erreur de l'executable detection afin de renvoyer ces informations sous la forme
    d'une liste d'image

    Args:
        resultat (str): résultat de la sortie standard et d'erreur de l'executable detection

    Returns:
        list[Image]: une liste d'image correspondant aux informations données en argument
    """
    tableau_ligne = resultat.split("\n")
    tableau_ligne_trie = [line for line in tableau_ligne if "frame" in line or line.endswith("1") or "Done" in line
                          or "detected" in line]

    tableau_image = [Image("", [])]
    compteur = 0
    for ligne in tableau_ligne_trie:
        if ligne.endswith("1") and not "frame" in ligne:
            infos_mire = ligne.split(" ")
            if int(infos_mire[2]) != -1 :
                tableau_image[compteur].mires_visibles.append(
                    (Mire2D(int(infos_mire[2]), (float(infos_mire[0]), float(infos_mire[1]))))
                )

        if ligne.startswith("Done"):
            chemin = ligne.split('/')
            tableau_image[compteur].name = chemin[-1]
            tableau_image[compteur].extension = chemin[-1].split(".")[-1] if "." in chemin[-1] else ''
            tableau_image[compteur].path = "/"+"/".join(chemin[1:])
            compteur += 1
            tableau_image.append(Image("", []))

    tableau_image.pop()

    #detection binary from CCTag automatically rotates images before detecting targets. Image coordinates has then to be corrected
    for im in tableau_image:
        im_width = exifImage(im.path).pixel_x_dimension
        im_height = exifImage(im.path).pixel_y_dimension
        if exifImage(im.path).orientation.value == 3:
            # case of a 180° rotation
            for mire in im.mires_visibles:
                # simply doing x' = width - x and y' = height - y
                mire.coordinates = np.subtract((im_width, im_height), mire.coordinates)
        elif exifImage(im.path).orientation.value != 1:
            # cases where orientation is neither 180° rotation neither "normal case" - theses cases are currently not managed
            print(f"""cas d'orientation d'image "{exifImage(im.path).orientation.name}" non traité""")

    return tableau_image

def save_liste_image(tableau_image:list[Image], aFile:File):
    with open(aFile.path, 'w') as f:
        for im in tableau_image:
            for mir in im.mires_visibles:
                f.write(f"{im.name},{mir.identifier},{mir.coordinates[0]:.3f},{mir.coordinates[1]:.3f}")
                f.write("\n")


def load_liste_image(aFile: File, path_images: str) -> list[Image]:
    tableau_image = []
    current_image = None

    with open(aFile.path, 'r') as f:
        for line in f:
            name, identifier, x, y = line.strip().split(',')
            if current_image is None or current_image.name != name:
                if current_image:
                    tableau_image.append(current_image)
                current_image = Image(path = os.sep.join([path_images,name]), mires_visibles=[])
            mire = Mire2D(identifier = int(identifier), coordinates=(float(x), float(y)))
            current_image.mires_visibles.append(mire)

    if current_image:
        tableau_image.append(current_image)

    return tableau_image

class DetectionCCTagException(Exception):
    pass


class DetectionCCTag(DetecteurMire):
    """
    Implémente l'interface DetecteurMire et implémente les méthodes nécessaires pour l'exécution de detection,
    une composante de CCTag

    Elle est utilisée pour calculer les coordonnées de chacune des mires présentes sur une image
    """

    def __init__(self, path_cctag_directory: str, working_directory: str, output_dir: str, reuse_wd: bool = False):
        """
        Initialise une instance de la classe DetectionCCTag

        Args:
            path_cctag_directory (str): le chemin vers le dossier contenant l'executable detection
            et ses librairies.

        Returns:
            None
        """
        super().__init__(working_directory, output_dir)
        check_module_executable_path(path_cctag_directory, "CCTag")
        self.path_cctag_directory = path_cctag_directory
        self.reuse_wd = reuse_wd

        if not reuse_wd:
            self.set_up_working_space()

    def detection_mires(self, chemin_dossier_image) -> list[Image]:
        """
        Détecte chacune des mires présentes sur une image, renvoyant une liste d'objet image contenant les mires
        (Mire2D) qui apparaissent sur cette image.

        Args:
            chemin_dossier_image: un dossier contenant une ou plusieurs images en paramètre.

        Returns:
            list[Image]: une liste contenant toutes les images ayant été trouvé par le détecteur de mire
        """
        if not self.reuse_wd:
            current_dir = os.path.abspath(os.curdir)
            chemin_absolue_dossier_image = os.path.abspath(chemin_dossier_image)
            os.chdir(self.path_cctag_directory)

            arguments = ["./detection", "-n", "3", "-i", chemin_absolue_dossier_image]
            process, output = self.subprocess(arguments, os.path.join(self.working_directory, "Detection.log"))
            if process.returncode != 0:
                raise_logged(logger.get_logger().critical,
                             DetectionCCTagException("Une erreur est survenu lors de la détection des mires dans les "
                                                     "images. Veuillez revoir les consignes "
                                                     "d'installation de la dépendance logicielle CCTag")
                             )
            liste_image = parsing_result(output)

            os.chdir(current_dir)

            os.makedirs(os.path.join(self.working_directory,os.path.split(chemin_dossier_image)[1]), exist_ok=True)
            cctagResults_filename = os.path.join(self.working_directory,os.path.split(chemin_dossier_image)[1],"cctag3CC_result.txt")
            save_liste_image(liste_image, File(cctagResults_filename))

            out_file = os.path.join(chemin_absolue_dossier_image, "cctag3CC.out")
            if path_exist(out_file):
                os.remove(out_file)

        else:
            liste_image=load_liste_image(File(os.path.join(self.working_directory, os.path.split(chemin_dossier_image)[1], "cctag3CC_result.txt")),os.path.abspath(chemin_dossier_image))

        return liste_image

    def get_config(self) -> str:
        return config_builer(self, "DetectionCCTag")

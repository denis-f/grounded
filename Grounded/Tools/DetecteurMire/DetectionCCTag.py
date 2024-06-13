import os

from Grounded.DataObject import Image
from Grounded.DataObject import Mire2D
from .DetecteurMire import DetecteurMire

import subprocess

from Grounded.utils import config_builer, check_module_executable_path


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
            tableau_image[compteur].mires_visibles.append(
                (Mire2D(int(infos_mire[2]), (float(infos_mire[0]), float(infos_mire[1]))))
            )

        if ligne.startswith("Done"):
            chemin = ligne.split('/')
            tableau_image[compteur].name = chemin[-1]
            tableau_image[compteur].extension = chemin[-1].split(".")[-1] if "." in chemin[-1] else ''
            tableau_image[compteur].path = "/".join(chemin[1:])
            compteur += 1
            tableau_image.append(Image("", []))

    tableau_image.pop()
    return tableau_image


class DetectionCCTag(DetecteurMire):
    """
    Implémente l'interface DetecteurMire et implémente les méthodes nécessaires pour l'exécution de detection,
    une composante de CCTag

    Elle est utilisée pour calculer les coordonnées de chacune des mires présentes sur une image
    """

    def __init__(self, path_cctag_directory: str):
        """
        Initialise une instance de la classe MicMac.

        Args:
            path_cctag_directory (str): le chemin vers le dossier contenant l'executable detection
            et ses librairies.

        Returns:
            None
        """
        check_module_executable_path(path_cctag_directory, "CCTag")

        self.path_cctag_directory = path_cctag_directory

    def detection_mires(self, chemin_dossier_image) -> list[Image]:
        """
        Détecte chacune des mires présentes sur une image, renvoyant une liste d'objet image contenant les mires
        (Mire2D) qui apparaissent sur cette image.

        Args:
            chemin_dossier_image: un dossier contenant une ou plusieurs images en paramètre.

        Returns:
            list[Image]: une liste contenant toutes les images ayant été trouvé par le détecteur de mire
        """
        current_dir = os.path.abspath(os.curdir)
        chemin_absolue_dossier_image = os.path.abspath(chemin_dossier_image)
        os.chdir(self.path_cctag_directory)
        process = subprocess.Popen(["./detection", "-n", "3", "-i", chemin_absolue_dossier_image],
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        liste_image = parsing_result(process.communicate()[0])
        os.chdir(current_dir)
        return liste_image

    def get_config(self) -> str:
        return config_builer(self, "DetectionCCTag")

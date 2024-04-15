import os

from src.DataObject import Image
from src.DataObject import Mire2D
from .DetecteurMire import DetecteurMire

import subprocess


def parsing_result(resultat: str) -> list[Image]:
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

    def __init__(self, detection_cctag_directory):
        self.detection_cctag_directory = detection_cctag_directory

    def detection_mires(self, chemin_dossier_image) -> list[Image]:
        current_dir = os.path.abspath(os.curdir)
        chemin_absolue_dossier_image = os.path.abspath(chemin_dossier_image)
        os.chdir(self.detection_cctag_directory)
        process = subprocess.Popen(["./detection", "-n", "3", "-i", chemin_absolue_dossier_image],
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        liste_image = parsing_result(process.communicate()[0])
        os.chdir(current_dir)
        return liste_image

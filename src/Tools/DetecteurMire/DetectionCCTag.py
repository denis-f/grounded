from src.DataObject import Image
from src.DataObject import Mire
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
                (Mire(int(infos_mire[2]), (float(infos_mire[0]), float(infos_mire[1]))))
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

    def detection_mires(self, chemin_dossier_image) -> list[Image]:
        process = subprocess.Popen(["./detection", "-n", "3", "-i", chemin_dossier_image], stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT,
                                   text=True)
        liste_image = parsing_result(process.communicate()[0])

        return liste_image

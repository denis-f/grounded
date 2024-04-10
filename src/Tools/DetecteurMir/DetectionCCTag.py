from src.DataObject import Image
from src.DataObject import Mir
import subprocess


def parsing_result(resultat: str) -> list[Image]:
    tableau_ligne = resultat.split("\n")
    tableau_ligne_trie = [line for line in tableau_ligne if "frame" in line or line.endswith("1") or "Done" in line
                          or "detected" in line]

    tableau_image = [Image("", "", [])]
    compteur = 0
    for ligne in tableau_ligne_trie:
        if ligne.endswith("1") and not "frame" in ligne:
            infos_mir = ligne.split(" ")
            tableau_image[compteur].mirs_visibles.append(
                (Mir(int(infos_mir[2]), (float(infos_mir[0]), float(infos_mir[1]))))
            )

        if ligne.startswith("Done"):
            chemin = ligne.split('/')
            tableau_image[compteur].nom = chemin[-1]
            tableau_image[compteur].chemin = "/".join(chemin[1:])
            compteur += 1
            tableau_image.append(Image("", "", []))

    tableau_image.pop()
    return tableau_image


class DetectionCCTag:

    def detection_mirs(self, chemin_dossier_image) -> list[Image]:
        process = subprocess.Popen(["./detection", "-n", "3", "-i", chemin_dossier_image], stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT,
                                 text=True)
        liste_image = parsing_result(process.communicate()[0])
        for image in liste_image:
            image.supprimer_mir_unique()

        return liste_image

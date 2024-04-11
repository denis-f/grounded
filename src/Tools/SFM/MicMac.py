import subprocess
import os

from .SFM import SFM
from src.DataObject import Image


def creer_dossier(dossier: str):
    os.makedirs(dossier, exist_ok=True)
    os.chmod(dossier, 0o777)



def effacer_fichier_si_existe(fichier: str):
    if os.path.exists(fichier):
        os.remove(fichier)


def creer_raccourci_dossier_dans_avec_prefix(dossier: str, dossier_raccourci: str, prefix: str):
    fichiers = os.listdir(dossier)
    # Boucle sur chaque fichier
    for nom_fichier in fichiers:
        chemin_complet_source = os.path.join(dossier, nom_fichier)
        chemin_complet_lien = os.path.join(dossier_raccourci, prefix + nom_fichier)
        effacer_fichier_si_existe(chemin_complet_lien)
        os.symlink(chemin_complet_source, chemin_complet_lien)


class MicMac(SFM):

    def __init__(self, repertoire_mm3d: str, chemin_dossier_avant: str, chemin_dossier_apres: str):
        self.repertoire_mm3d = repertoire_mm3d
        self.log_dir = os.path.abspath(os.path.join(os.curdir, "log_micmac"))

        creer_dossier(self.log_dir)  # création du dossier de log micmac
        creer_raccourci_dossier_dans_avec_prefix(os.path.abspath(chemin_dossier_avant), self.log_dir, "0_")
        creer_raccourci_dossier_dans_avec_prefix(os.path.abspath(chemin_dossier_apres), self.log_dir, "1_")

    def detection_points_homologues(self):
        subprocess.run([f"{self.repertoire_mm3d}mm3d", "Tapioca", "All",
                        f"{self.log_dir}/.*JPG", "1000"])

    def calibration(self):
        pass

    def generer_nuages_de_points(self):
        pass

    def calculer_coordonnees_3d_mirs(self, image: Image):
        log_directory = os.path.join(self.log_dir, "calcul_coordonnees")

        # créer le dossier de log si il n'existe pas
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)
        nom_fichier_coordonnees = os.path.join(log_directory, f"{image.get_nom_image_sans_extension()}_coord.txt")
        with open(nom_fichier_coordonnees, 'w') as file:
            file.write(image.get_string_coordonnees_mirs())

        nom_fichier_coordonnees_3d = os.path.join(log_directory, f"{image.get_nom_image_sans_extension()}_3D_coord.txt")
        subprocess.run(["mm3d", "Im2XYZ", f"PIMs-QuickMac/Nuage-Depth-{image.nom}.xml",
                        nom_fichier_coordonnees, nom_fichier_coordonnees_3d])

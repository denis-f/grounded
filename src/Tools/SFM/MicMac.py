from .SFM import SFM
from src.DataObject import Image
from src.DataObject import PointCloud

import subprocess
import os


def copier_contenu_dossier(dossier_source: str, dossier_destination: str):
    contenu_dossier_source = os.listdir(dossier_source)

    # Boucle sur chaque élément du dossier source
    for element in contenu_dossier_source:
        # Chemin complet de l'élément dans le dossier source
        chemin_complet_source = os.path.join(dossier_source, element)
        # Chemin complet de l'élément dans le dossier destination
        chemin_complet_destination = os.path.join(dossier_destination, element)
        # Déplace l'élément dans le dossier destination
        os.rename(chemin_complet_source, chemin_complet_destination)


def renommer_fichier(fichier: str, nouveau_nom: str):
    try:
        os.rename(fichier, nouveau_nom)
    except OSError as e:
        raise Exception("Un problème est survenue lors du renommage du fichier")


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

    def __init__(self, chemin_mm3d: str, chemin_dossier_avant: str, chemin_dossier_apres: str):
        self.chemin_mm3d = chemin_mm3d
        self.working_directory = os.path.abspath(os.path.join(os.curdir, "micmac_working_directory"))

        os.makedirs(self.working_directory, exist_ok=True)  # création du dossier de l'espace de travail micmac

        # création des raccourcis pour les fichiers avant
        creer_raccourci_dossier_dans_avec_prefix(os.path.abspath(chemin_dossier_avant), self.working_directory, "0_")

        # creation des raccourcis pour les fichiers après
        creer_raccourci_dossier_dans_avec_prefix(os.path.abspath(chemin_dossier_apres), self.working_directory, "1_")

    def detection_points_homologues(self):
        subprocess.run([self.chemin_mm3d, "Tapioca", "All",
                        f"{self.working_directory}{os.sep}.*JPG", "1000"])

    def calibration(self):
        subprocess.run([self.chemin_mm3d, "Tapas", "FraserBasic", f"{self.working_directory}/.*JPG"])

    def generer_nuages_de_points(self) -> tuple[PointCloud, PointCloud]:
        # On génère le nuage de points des photos d'avant excavation
        subprocess.run([self.chemin_mm3d, "C3DC", "QuickMac", f"{self.working_directory}{os.sep}0_.*JPG", "FraserBasic"])

        # On renomme le fichier C3DC_QuickMac.ply généré automatiquement en C3DC_0.ply
        renommer_fichier(os.path.join(self.working_directory, "C3DC_QuickMac.ply"), os.path.join(self.working_directory, "C3DC_0.ply"))

        # On déplace le fichier PIMs-QuickMac en Tempo de façon temporaire afin de générer le nuage de point d'après
        # excavation sans effets de bords
        renommer_fichier(os.path.join(self.working_directory, "PIMs-QuickMac"), os.path.join(self.working_directory, "Tempo"))

        # On génère le nuage de points des photos d'après excavation
        subprocess.run([self.chemin_mm3d, "C3DC", "QuickMac", f"{self.working_directory}{os.sep}1_.*JPG", "FraserBasic"])

        # On renomme le fichier C3DC_QuickMac.ply généré automatiquement en C3DC_1.ply
        renommer_fichier(os.path.join(self.working_directory, "C3DC_QuickMac.ply"), os.path.join(self.working_directory, "C3DC_1.ply"))

        # On déplace le contenu de Tempo à l'intérieur de PIMs-QuickMac sans les fichiers pouvant générer des conflits
        effacer_fichier_si_existe(os.path.join(self.working_directory, "Tempo", "PimsEtat.xml"))
        effacer_fichier_si_existe(os.path.join(self.working_directory, "Tempo", "PimsFile.xml"))
        copier_contenu_dossier(os.path.join(self.working_directory, "Tempo"), os.path.join(self.working_directory, "PIMs-QuickMac"))

        # On supprime le dossier Tempo
        os.rmdir(os.path.join(self.working_directory, "Tempo"))

        return PointCloud(os.path.join(self.working_directory, "C3DC_0.ply")), PointCloud(os.path.join(self.working_directory, "C3DC_1.ply"))

    def calculer_coordonnees_3d_mires(self, image: Image):
        log_directory = os.path.join(self.working_directory, "calcul_coordonnees")

        # créer le dossier de log s'il n'existe pas
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)
        nom_fichier_coordonnees = os.path.join(log_directory, f"{image.get_nom_image_sans_extension()}_coord.txt")
        with open(nom_fichier_coordonnees, 'w') as file:
            file.write(image.get_string_coordonnees_mirs())

        nom_fichier_coordonnees_3d = os.path.join(log_directory, f"{image.get_nom_image_sans_extension()}_3D_coord.txt")
        subprocess.run(["mm3d", "Im2XYZ", f"PIMs-QuickMac{os.sep}Nuage-Depth-{image.name}.xml",
                        nom_fichier_coordonnees, nom_fichier_coordonnees_3d])

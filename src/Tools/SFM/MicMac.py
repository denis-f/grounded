from .SFM import SFM
from src.DataObject import Image, File, PointCloud, Mire2D, Mire3D

import subprocess
import os


def recuperer_mires_3d(image: Image, fichier_coordonnees_2d, fichier_coordonnees_3d, fichier_filtered) -> list[Mire3D]:
    if not os.path.exists(fichier_coordonnees_3d):  # si le fichier contenant les coordonnées 3d n'est pas trouvé
        raise FileNotFoundError(f"le fichier \"{fichier_coordonnees_3d}\" est introuvable")

    # on ouvre le fichier de coordonnées 3d pour récupérer son contenu
    with open(fichier_coordonnees_3d) as file:
        contenu = file.read()

    mires = []
    # si le fichier de coordonnées 3D est vide, aucune coordonnées n'est retrouvé, donc on renvoie une liste vide
    if len(contenu) == 0:
        return mires

    # ici, on parse les coordonnées 3d
    coordonnees_3d = []
    if len(contenu) > 0:
        tableau_coordonnees = contenu.split("\n")
        for ligne_tableau in tableau_coordonnees:
            coordonnees_separes = ligne_tableau.split(" ")
            if len(coordonnees_separes) == 3:
                coordonnees_3d.append((float(coordonnees_separes[0]), float(coordonnees_separes[1]),
                                       float(coordonnees_separes[2])))

    # si le fichier filtered n'existe pas, mais que le fichier de coordonnées 3d est non vide alors les coordonnées
    # sont dans le même ordre que stocké dans la liste de mires visibles dans l'image
    if not os.path.exists(fichier_filtered):
        for i in range(len(image.mires_visibles)):
            mire_courante = image.mires_visibles[i]
            mires.append(Mire3D(mire_courante.identifiant, (coordonnees_3d[i][0],
                                                            coordonnees_3d[i][1],
                                                            coordonnees_3d[i][2])))
        return mires

    # si nous ne sommes dans aucun des cas suivant, alors seulement certaines coordonnées n'ont pas pu être reconnu,
    # il est donc nécessaire de vérifier par comparaison à quels mires sont associées chacune des coordonnées

    # pour faire cela, on récupère le contenu du fichier filtered
    with open(fichier_filtered) as file:
        contenu = file.read()

    # on parse les coordonnées du fichier filtered
    coordonnees_filtered = []
    if len(contenu) > 0:
        tableau_coordonnees = contenu.split("\n")
        for ligne_tableau in tableau_coordonnees:
            coordonnees_separes = ligne_tableau.split(" ")
            if len(coordonnees_separes) == 2:
                coordonnees_filtered.append((float(coordonnees_separes[0]), float(coordonnees_separes[1])))

    # on associe chacune des coordonnées à son identifiant
    for i in range(len(coordonnees_filtered)):
        coordonnees_2d = coordonnees_filtered[i]
        for mir_2d in image.mires_visibles:
            if mir_2d.coordonnees[0] == coordonnees_2d[0] and mir_2d.coordonnees[1] == coordonnees_2d[1]:
                mires.append(Mire3D(mir_2d.identifiant, (coordonnees_3d[i][0],
                                                         coordonnees_3d[i][1],
                                                         coordonnees_3d[i][2])))

    return mires


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


def recuperer_premier_fichier_avec_pattern(source_directory: str, pattern: str):
    files = os.listdir(source_directory)
    for file_name in files:
        if pattern in file_name:
            try:
                return File(os.path.join(source_directory, file_name))
            except FileNotFoundError:
                raise Exception("Fichier introuvable")


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

    def __init__(self, chemin_mm3d: str):
        self.chemin_mm3d = chemin_mm3d
        self.working_directory = os.path.abspath(os.path.join(os.curdir, "micmac_working_directory"))

    def detection_points_homologues(self, chemin_dossier_avant: str, chemin_dossier_apres: str):
        os.makedirs(self.working_directory, exist_ok=True)  # création du dossier de l'espace de travail micmac

        # création des raccourcis pour les fichiers avant
        creer_raccourci_dossier_dans_avec_prefix(os.path.abspath(chemin_dossier_avant), self.working_directory, "0_")

        # creation des raccourcis pour les fichiers après
        creer_raccourci_dossier_dans_avec_prefix(os.path.abspath(chemin_dossier_apres), self.working_directory, "1_")

        subprocess.run([self.chemin_mm3d, "Tapioca", "All",
                        f"{self.working_directory}{os.sep}.*JPG", "1000"])

    def calibration(self):
        subprocess.run([self.chemin_mm3d, "Tapas", "FraserBasic", f"{self.working_directory}/.*JPG"])

    def generer_nuages_de_points(self) -> tuple[PointCloud, PointCloud]:
        # On génère le nuage de points des photos d'avant excavation
        subprocess.run(
            [self.chemin_mm3d, "C3DC", "QuickMac", f"{self.working_directory}{os.sep}0_.*JPG", "FraserBasic"])

        # On renomme le fichier C3DC_QuickMac.ply généré automatiquement en C3DC_0.ply
        renommer_fichier(os.path.join(self.working_directory, "C3DC_QuickMac.ply"),
                         os.path.join(self.working_directory, "C3DC_0.ply"))

        # On déplace le fichier PIMs-QuickMac en Tempo de façon temporaire afin de générer le nuage de point d'après
        # excavation sans effets de bords
        renommer_fichier(os.path.join(self.working_directory, "PIMs-QuickMac"),
                         os.path.join(self.working_directory, "Tempo"))

        # On génère le nuage de points des photos d'après excavation
        subprocess.run(
            [self.chemin_mm3d, "C3DC", "QuickMac", f"{self.working_directory}{os.sep}1_.*JPG", "FraserBasic"])

        # On renomme le fichier C3DC_QuickMac.ply généré automatiquement en C3DC_1.ply
        renommer_fichier(os.path.join(self.working_directory, "C3DC_QuickMac.ply"),
                         os.path.join(self.working_directory, "C3DC_1.ply"))

        # On déplace le contenu de Tempo à l'intérieur de PIMs-QuickMac sans les fichiers pouvant générer des conflits
        effacer_fichier_si_existe(os.path.join(self.working_directory, "Tempo", "PimsEtat.xml"))
        effacer_fichier_si_existe(os.path.join(self.working_directory, "Tempo", "PimsFile.xml"))
        copier_contenu_dossier(os.path.join(self.working_directory, "Tempo"),
                               os.path.join(self.working_directory, "PIMs-QuickMac"))

        # On supprime le dossier Tempo
        os.rmdir(os.path.join(self.working_directory, "Tempo"))

        return PointCloud(os.path.join(self.working_directory, "C3DC_0.ply")), PointCloud(
            os.path.join(self.working_directory, "C3DC_1.ply"))

    def calculer_coordonnees_3d_mires(self, image: Image) -> list[Mire3D]:
        log_directory = os.path.join(self.working_directory, "calcul_coordonnees")

        # créer le dossier de log s'il n'existe pas
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)
        nom_fichier_coordonnees = os.path.join(log_directory, f"{image.get_nom_image_sans_extension()}_coord.txt")

        # on crée le fichier qui va contenir les coordonnées 2D de notre image.
        with open(nom_fichier_coordonnees, 'w') as file:
            file.write(image.get_string_coordonnees_mires())

        # On récupère le nom de l'image dans l'espace de travail MicMac
        image_locale = recuperer_premier_fichier_avec_pattern(self.working_directory,
                                                              image.get_nom_image_sans_extension())

        # on génère nos coordonnées 3D dans un fichier
        nom_fichier_coordonnees_3d = os.path.join(log_directory, f"{image.get_nom_image_sans_extension()}_3D_coord.txt")
        subprocess.run([self.chemin_mm3d, "Im2XYZ", os.path.join(self.working_directory,
                                                                 f"PIMs-QuickMac{os.sep}Nuage-Depth-"
                                                                 f"{image_locale.name}.xml"),
                        nom_fichier_coordonnees, nom_fichier_coordonnees_3d])

        nom_fichier_filtered = os.path.join(log_directory, f"Filtered_{image.get_nom_image_sans_extension()}_coord.txt")

        return recuperer_mires_3d(image, nom_fichier_coordonnees, nom_fichier_coordonnees_3d, nom_fichier_filtered)

from .SFM import SFM
from Grounded.DataObject import Image, File, PointCloud, Mire2D, Mire3D
from Grounded.utils import find_files_regex, rename_file, config_builer, check_module_executable_path, raise_logged, parse_bool
import Grounded.logger as logger

import subprocess
import os
import shutil


def recuperer_mires_3d(image: Image, fichier_coordinates_3d, fichier_filtered) -> (list[Mire2D], list[Mire3D]):

    mires2d = []
    mires3d = []
    if not os.path.exists(fichier_coordinates_3d):  # si le fichier contenant les coordonnées 3d n'est pas trouvé
        return mires2d, mires3d

    # on ouvre le fichier de coordonnées 3d pour récupérer son contenu
    with open(fichier_coordinates_3d) as file:
        contenu = file.read()

    # si le fichier de coordonnées 3D est vide, aucune coordonnées n'est retrouvé, donc on renvoie une liste vide
    if len(contenu) == 0:
        return mires2d, mires3d

    # ici, on parse les coordonnées 3d
    coordinates_3d = []
    if len(contenu) > 0:
        tableau_coordinates = contenu.split("\n")
        for ligne_tableau in tableau_coordinates:
            coordinates_separes = ligne_tableau.split(" ")
            if len(coordinates_separes) == 3:
                coordinates_3d.append((float(coordinates_separes[0]), float(coordinates_separes[1]),
                                       float(coordinates_separes[2])))

    # si le fichier filtered n'existe pas, mais que le fichier de coordonnées 3d est non vide alors les coordonnées
    # sont dans le même ordre que stocké dans la liste de mires visibles dans l'image
    if not os.path.exists(fichier_filtered):
        for i in range(len(image.mires_visibles)):
            mire_courante = image.mires_visibles[i]
            mires2d.append(mire_courante)
            mires3d.append(Mire3D(mire_courante.identifier, (coordinates_3d[i][0],
                                                           coordinates_3d[i][1],
                                                           coordinates_3d[i][2])))
        return mires2d,mires3d

    # si nous ne sommes dans aucun des cas suivant, alors seulement certaines coordonnées n'ont pas pu être reconnu,
    # il est donc nécessaire de vérifier par comparaison à quels mires sont associées chacune des coordonnées

    # pour faire cela, on récupère le contenu du fichier filtered
    with open(fichier_filtered) as file:
        contenu = file.read()

    # on parse les coordonnées du fichier filtered
    coordinates_filtered = []
    if len(contenu) > 0:
        tableau_coordinates = contenu.split("\n")
        for ligne_tableau in tableau_coordinates:
            coordinates_separes = ligne_tableau.split(" ")
            if len(coordinates_separes) == 2:
                coordinates_filtered.append((float(coordinates_separes[0]), float(coordinates_separes[1])))

    # on associe chacune des coordonnées à son identifiant
    for i in range(len(coordinates_filtered)):
        coordinates_2d = coordinates_filtered[i]
        for mir_2d in image.mires_visibles:
            if mir_2d.coordinates[0] == coordinates_2d[0] and mir_2d.coordinates[1] == coordinates_2d[1]:
                mires2d.append(mir_2d)
                mires3d.append(Mire3D(mir_2d.identifier, (coordinates_3d[i][0],
                                                        coordinates_3d[i][1],
                                                        coordinates_3d[i][2])))

    return mires2d,mires3d


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


distorsion_model_values = ["RadialExtended", "RadialBasic", "Fraser", "FraserBasic", "FishEyeEqui",
                           "HemiEqui", "AutoCal", "Figee"]

zoom_final_values = ["QuickMac", "MicMac", "BigMac"]

tapioca_mode_values = ["All", "MulScale"]

micmac_img_extensions_regex = "(.*JPG|.*tif|.*jpg|.*TIF)"


class MicMacException(Exception):

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class MicMac(SFM):
    """
    Implémente l'interface SFM et implémente les méthodes nécessaires pour l'exécution de MicMac,
    un logiciel de photogrammétrie.

    Elle est utilisée pour effectuer diverses opérations telles que la détection de points homologues, la calibration
    de la caméra, la génération de nuages de points, et le calcul des coordonnées 3D des mires dans une image.
    """

    def __init__(self, path_mm3d: str, working_directory: str, output_dir: str, distorsion_model: str = "FraserBasic",
                 zoom_final: str = "QuickMac", tapioca_mode: str = "All", tapioca_resolution: str = "1000",
                 tapioca_second_resolution: str ="1000", reuse_wd: str ="False"):
        """
        Initialise une instance de la classe MicMac.

        Args:
            working_directory (str): répertoire de travail
            output_dir (str): fichier de sortie
            tapioca_mode (str): mode utilisé par la commande tapioca
            tapioca_resolution (str): résolution utilisée par la commande tapioca
            tapioca_second_resolution (str): seconde résolution utilisée par la commande tapioca, uniquement avec le mode MulScale
            path_mm3d (str): Le chemin vers l'exécutable MicMac.
            distorsion_model (str): un modèle de distorsion
            zoom_final (str): un zoom final
            reuse_wd (bool): pour ré-utiliser les calculs de micmac plutôt que tout recalculer


        Returns:
            None
        """
        if distorsion_model not in distorsion_model_values:
            raise ValueError(
                f"Invalid distortion model: {distorsion_model} provided. Allowed values are {distorsion_model_values}.")

        if zoom_final not in zoom_final_values:
            raise ValueError(
                f"Invalid zoom final: {zoom_final} provided. Allowed values are {zoom_final_values}.")

        if tapioca_mode not in tapioca_mode_values:
            raise ValueError(
                f"Invalid tapioca mode: {tapioca_mode} provided. Allowed values are {tapioca_mode_values}.")



        check_module_executable_path(path_mm3d, "MicMac")

        super().__init__(working_directory, output_dir)
        self.path_mm3d = path_mm3d
        self.distorsion_model = distorsion_model
        self.tapioca_mode = tapioca_mode
        self.tapioca_resolution = tapioca_resolution
        self.tapioca_second_resolution = tapioca_second_resolution
        self.zoom_final = zoom_final
        try:
            self.reuse_wd = parse_bool(reuse_wd)
        except ValueError:
            raise ValueError(f"Invalid reuse_wd. {reuse_wd} is not a boolean.")


        if not self.reuse_wd:
            self.set_up_working_space()

    def detection_points_homologues(self, chemin_dossier_avant: str, chemin_dossier_apres: str):
        """
        Méthode pour détecter les points homologues entre des images avant et après un événement  .

        Args:
            chemin_dossier_avant (str): Le chemin vers le dossier contenant les images avant excavation.
            chemin_dossier_apres (str): Le chemin vers le dossier contenant les images après excavation.

        Returns:
            None
        """
        print("Détection des points homologues en cours, cela peut prendre un certain temps. Veuillez patienter...")
        self.set_up_working_space()

        # création des raccourcis pour les fichiers avant
        creer_raccourci_dossier_dans_avec_prefix(chemin_dossier_avant, self.working_directory, "0_")

        # creation des raccourcis pour les fichiers après
        creer_raccourci_dossier_dans_avec_prefix(chemin_dossier_apres, self.working_directory, "1_")

        arguments = [self.path_mm3d, "Tapioca", self.tapioca_mode,
                     f"{self.working_directory}{os.sep}{micmac_img_extensions_regex}", self.tapioca_resolution]

        if self.tapioca_mode == 'MulScale':
            arguments.append(self.tapioca_second_resolution)

        process = self.subprocess(arguments, os.path.join(self.working_directory, "Tapioca.log"))[0]
        if process.returncode != 0:
            raise_logged(logger.get_logger().critical,
                         MicMacException("Une erreur est survenu lors de la détection des points homologues, "
                                         "veuillez vérifier votre jeu de données")
                         )

    def calibration(self):
        """
        Méthode pour calibrer la caméra.

        Returns:
            None
        """
        print("Calibration en cours, cela peut prendre un certain temps. Veuillez patienter...")
        arguments = [self.path_mm3d, "Tapas", self.distorsion_model, f"{self.working_directory}{os.sep}{micmac_img_extensions_regex}"]
        process = self.subprocess(arguments, os.path.join(self.working_directory, "Tapas.log"))[0]
        if process.returncode != 0:
            raise_logged(logger.get_logger().critical,
                         MicMacException("Une erreur est survenu lors de la détection de la caméra,"
                                         "veuillez vérifier votre jeu de données")
                         )

    def generer_nuages_de_points(self, chemin_dossier_avant: str, chemin_dossier_apres: str) -> tuple[
        PointCloud, PointCloud]:
        """
        Méthode pour générer des nuages de points avant/après excavation.

        Args:
            chemin_dossier_avant (str): Le chemin vers le dossier contenant les images avant excavation.
            chemin_dossier_apres (str): Le chemin vers le dossier contenant les images après excavation.

        Returns:
            Tuple[NuageDePoints, NuageDePoints]: Un tuple contenant deux objets NuageDePoints représentant les nuages de points
            avant et après excavation.
            tuple[0] ⇛ avant et tuple[1] ⇛ après
        """
        if not self.reuse_wd :
            self.detection_points_homologues(chemin_dossier_avant, chemin_dossier_apres)
            self.calibration()

            print("Génération des nuages de point en cours, cela peut prendre un certain temps. Veuillez patienter...")

            # On génère le nuage de points des photos d'avant excavation
            arguments = [self.path_mm3d, "C3DC", self.zoom_final, f"{self.working_directory}{os.sep}0_{micmac_img_extensions_regex}",
                         self.distorsion_model]
            process = self.subprocess(arguments, os.path.join(self.working_directory, "C3DC_0.log"))[0]
            if process.returncode != 0:
                raise_logged(logger.get_logger().critical,
                             MicMacException("Une erreur est survenu lors de la génération du nuage de "
                                             "points avant excavation, veuillez vérifier votre jeu de données")
                             )

            # On renomme le fichier C3DC_{self.zoom_final}.ply généré automatiquement en C3DC_0.ply
            rename_file(os.path.join(self.working_directory, f"C3DC_{self.zoom_final}.ply"), "C3DC_0")

            # On déplace le fichier PIMs-{self.zoom_final} en Tempo de façon temporaire afin de générer le nuage de point
            # d'après excavation sans effets de bords
            os.rename(os.path.join(self.working_directory, f"PIMs-{self.zoom_final}"),
                      os.path.join(self.working_directory, "Tempo"))

            # On génère le nuage de points des photos d'après excavation
            arguments = [self.path_mm3d, "C3DC", self.zoom_final, f"{self.working_directory}{os.sep}1_{micmac_img_extensions_regex}",
                         self.distorsion_model]

            self.subprocess(arguments, os.path.join(self.working_directory, "C3DC_1.log"))

            if process.returncode != 0:
                raise_logged(logger.get_logger().critical,
                             MicMacException("Une erreur est survenu lors de la génération du nuage de "
                                             "points après excavation, veuillez vérifier votre jeu de données")
                             )

            # On renomme le fichier C3DC_{self.zoom_final}.ply généré automatiquement en C3DC_1.ply
            rename_file(os.path.join(self.working_directory, f"C3DC_{self.zoom_final}.ply"), "C3DC_1")

            # On déplace le contenu de Tempo à l'intérieur de PIMs-{self.zoom_final} sans les fichiers pouvant générer
            # des conflits
            effacer_fichier_si_existe(os.path.join(self.working_directory, "Tempo", "PimsEtat.xml"))
            effacer_fichier_si_existe(os.path.join(self.working_directory, "Tempo", "PimsFile.xml"))
            copier_contenu_dossier(os.path.join(self.working_directory, "Tempo"),
                                   os.path.join(self.working_directory, f"PIMs-{self.zoom_final}"))

            # On supprime le dossier Tempo
            os.rmdir(os.path.join(self.working_directory, "Tempo"))

        else:
            print("Micmac - reprise des calculs existants (points homologues, orientation, nuages de points)")

        return PointCloud(os.path.join(self.working_directory, "C3DC_0.ply")), PointCloud(
            os.path.join(self.working_directory, "C3DC_1.ply"))

    def calculer_coordinates_3d_mires(self, image: Image) -> (list[Mire2D],list[Mire3D]):
        """
        Méthode pour calculer les coordonnées 3D des cibles dans une image.

        Args:
            image (Image): un objet Image contenant des cibles

        Returns:
            List[Mire3D]: Une liste d'objets Mire3D contenant les coordonnées 3D des cibles.
        """
        log_directory = os.path.join(self.working_directory, "calcul_coordinates")

        # créer le dossier de log s'il n'existe pas
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)
        nom_fichier_coordinates = os.path.join(log_directory, f"{image.get_name_without_extension()}_coord.txt")

        # on crée le fichier qui va contenir les coordonnées 2D de notre image.
        with open(nom_fichier_coordinates, 'w') as file:
            file.write(image.get_string_coordinates_mires())

        # On récupère le nom de l'image dans l'espace de travail MicMac
        image_locale = File(find_files_regex(self.working_directory, image.get_name_without_extension())[0])

        # Micmac va créer un fichier de coordonnées 3D et éventuellement un fichier Filtered (si certains points 2D ne peuvent pas être calculés)
        nom_fichier_coordinates_3d = os.path.join(log_directory, f"{image.get_name_without_extension()}_3D_coord.txt")
        nom_fichier_filtered = os.path.join(log_directory, f"Filtered_{image.get_name_without_extension()}_coord.txt")
        # Si ces fichiers existent déjà (Filtered et 3D_coord), on les supprime pour éviter des bugs liés au recalcul des coordonnées 3D
        # TODO idéalement ces calculs ne devraient pas être strictement dans l'espace de travail micmac puisque c'est un mix entre SFM et Detector ?
        if os.path.exists(nom_fichier_coordinates_3d):
            os.remove(nom_fichier_coordinates_3d)
        if os.path.exists(nom_fichier_filtered):
            os.remove(nom_fichier_filtered)

        # on génère nos coordonnées 3D dans un fichier
        process = self.subprocess([self.path_mm3d, "Im2XYZ", os.path.join(self.working_directory,
                                                                          f"PIMs-{self.zoom_final}{os.sep}Nuage-Depth-"
                                                                          f"{image_locale.name}.xml"),
                                   nom_fichier_coordinates, nom_fichier_coordinates_3d],
                                  os.path.join(self.working_directory, "Im2XYZ.log"))[0]

        try:
            return recuperer_mires_3d(image, nom_fichier_coordinates_3d, nom_fichier_filtered)
        except FileNotFoundError:
            if len(image.mires_visibles) > 0:
                logger.get_logger().warning(f"Aucune mire visible dans la photo {image.name} "
                                            f"n'a pu êre reporté dans l'espace 3D")
            return []


    def get_config(self) -> str:
        return config_builer(self, "MicMac")


    def subprocess(self, arguments: list, out_file: str):
        current_dir = os.path.abspath(os.curdir)
        os.chdir(self.working_directory)
        process, out = super().subprocess(arguments, out_file)
        os.chdir(current_dir)
        return process, out

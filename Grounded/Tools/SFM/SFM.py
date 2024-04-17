from abc import ABC, abstractmethod
from Grounded.DataObject import Image, PointCloud, Mire3D


class SFM(ABC):
    """
    Cette classe est une interface permettant d'interchanger les différents outils de type "SFM".
    Les méthodes abstraites définies au sein de cette classe devront être implémenté par toutes les classes
    non abstraites qui hériteront de cette classe
    """

    @abstractmethod
    def detection_points_homologues(self, chemin_dossier_avant: str, chemin_dossier_apres: str):
        """
        Méthode abstraite pour détecter les points homologues entre des images avant et après un événement.

        Arguments :
            chemin_dossier_avant (str): Le chemin vers le dossier contenant les images avant excavation.
            chemin_dossier_apres (str): Le chemin vers le dossier contenant les images après excavation.

        Returns :
            None
        """
        pass

    @abstractmethod
    def calibration(self, distorsion_model):
        """
        Méthode abstraite pour calibrer la caméra.

        Arguments:
            distorsion_model (str): Le modèle de distorsion à utiliser pour la calibration.

        Returns:
            None
        """
        pass

    @abstractmethod
    def generer_nuages_de_points(self, zoom_final: str) -> tuple[PointCloud, PointCloud]:
        """
        Méthode pour générer des nuages de points avant/après excavation.

        Arguments:
            zoom_final (str): Le niveau de zoom final pour la génération des nuages de points.

        Returns:
            tuple[PointCloud, PointCloud]: Un tuple contenant deux objets PointCloud représentant les nuages de points
            avant et après excavation.
            tuple[0] ⇛ avant et tuple[1] ⇛ après
        """
        pass

    @abstractmethod
    def calculer_coordinates_3d_mires(self, image: Image) -> list[Mire3D]:
        """
        Méthode abstraite pour calculer les coordonnées 3D des mires d'une image.

        Arguments:
            image (Image): une image de type Image contenant des mires

        Returns:
            list[Mire3D]: Une liste d'objets Mire3D contenant les coordonnées 3D des mires.
         """
        pass

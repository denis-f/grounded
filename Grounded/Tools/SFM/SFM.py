from abc import ABC, abstractmethod
from Grounded.DataObject import Image, PointCloud, Mire3D
from Grounded.Tools.Tools import Tools


class SFM(Tools, ABC):
    """
    Interface pour les différents outils de Structure from Motion (SFM).

    Les méthodes abstraites définies ici doivent être implémentées par toutes les classes
    non abstraites héritant de cette interface.
    """

    @abstractmethod
    def generer_nuages_de_points(self, chemin_dossier_avant: str, chemin_dossier_apres: str) -> tuple[PointCloud, PointCloud]:
        """
        Génère des nuages de points avant/après excavation.

        Args :
            chemin_dossier_avant (str): Chemin vers le dossier contenant les images avant l'excavation.
            chemin_dossier_apres (str): Chemin vers le dossier contenant les images après l'excavation.

        Returns:
            tuple[PointCloud, PointCloud]: Un tuple contenant deux objets PointCloud représentant les nuages de points
            avant et après excavation.
            tuple[0] ⇛ avant et tuple[1] ⇛ après
        """
        pass

    @abstractmethod
    def calculer_coordinates_3d_mires(self, image: Image) -> list[Mire3D]:
        """
        Calcule les coordonnées 3D des mires dans une image.

        Args:
            image (Image): Une image contenant des mires.

        Returns:
            list[Mire3D]: Une liste d'objets Mire3D contenant les coordonnées 3D des mires.
        """
        pass

    @abstractmethod
    def get_config(self) -> str:
        pass

from abc import ABC, abstractmethod
from Grounded.DataObject import PointCloud, Raster


class PointCloudProcessor(ABC):
    """
    Cette classe est une interface définissant les méthodes nécessaires pour traiter les nuages de points.

    Les classes concrètes implémentant cette interface devront fournir des implémentations pour les méthodes
    mise_a_echelle et cloud_to_cloud_difference.
    """

    @abstractmethod
    def mise_a_echelle(self, point_cloud: PointCloud, facteur: float) -> PointCloud:
        """
        Méthode abstraite pour effectuer une mise à l'échelle d'un nuage de points.

        Args:
            point_cloud (PointCloud): Le nuage de points à mettre à l'échelle.
            facteur (float): Le facteur d'échelle à appliquer.

        Returns:
            PointCloud: Le nuage de points mis à l'échelle.
        """
        pass

    @abstractmethod
    def cloud_to_cloud_distance(self, point_cloud_before_excavation: PointCloud,
                                point_cloud_after_excavation: PointCloud) -> Raster:
        """
        Méthode abstraite pour calculer la distance entre deux nuages de points.

        Args:
            point_cloud_before_excavation (PointCloud): Le nuage de points avant l'excavation.
            point_cloud_after_excavation (PointCloud): Le nuage de points après l'excavation.

        Returns:
            Raster: Un objet Raster correspondant à un fichier raster représentant la distance
            entre les deux nuages de points.
        """
        pass

    @abstractmethod
    def crop_point_cloud(self, point_cloud: PointCloud, coordonnees_trace: list[tuple[float, float]]) -> PointCloud:
        pass

    @abstractmethod
    def volume_between_clouds(self, crop_before: PointCloud, crop_after: PointCloud) -> float:
        """
        Méthode abstraite pour calculer le volume se trouvant entre deux nuages de points

        Args:
            crop_before (PointCloud): Le nuage de points découpé avant l'excavation.
            crop_after (PointCloud): Le nuage de points découpé après l'excavation.

        Returns:
            float: le volume calculé
        """
        pass

    @abstractmethod
    def get_config(self) -> str:
        pass

from abc import ABC, abstractmethod
from Grounded.DataObject import PointCloud


class TraiteurNuage3D(ABC):

    @abstractmethod
    def mise_a_echelle(self, point_cloud: PointCloud, facteur: float) -> PointCloud:
        pass

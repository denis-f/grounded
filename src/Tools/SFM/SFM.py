from abc import ABC, abstractmethod
from src.DataObject import Image
from src.DataObject import PointCloud


class SFM(ABC):

    @abstractmethod
    def detection_points_homologues(self):
        pass

    @abstractmethod
    def calibration(self):
        pass

    @abstractmethod
    def generer_nuages_de_points(self) -> tuple[PointCloud, PointCloud]:
        pass

    @abstractmethod
    def calculer_coordonnees_3d_mires(self, image: Image):
        pass

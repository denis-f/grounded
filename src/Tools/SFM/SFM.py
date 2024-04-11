from abc import ABC, abstractmethod
from src.DataObject import Image


class SFM(ABC):

    @abstractmethod
    def detection_points_homologues(self):
        pass

    @abstractmethod
    def calibration(self):
        pass

    @abstractmethod
    def generer_nuages_de_points(self):
        pass

    @abstractmethod
    def calculer_coordonnees_3d_mirs(self, image: Image):
        pass

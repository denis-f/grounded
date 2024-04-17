from abc import ABC, abstractmethod
from Grounded.DataObject import Image, PointCloud, Mire3D


class SFM(ABC):

    @abstractmethod
    def detection_points_homologues(self, chemin_dossier_avant: str, chemin_dossier_apres: str):
        pass

    @abstractmethod
    def calibration(self, distorsion_model):
        pass

    @abstractmethod
    def generer_nuages_de_points(self, zoom_final: str) -> tuple[PointCloud, PointCloud]:
        pass

    @abstractmethod
    def calculer_coordinates_3d_mires(self, image: Image) -> list[Mire3D]:
        pass

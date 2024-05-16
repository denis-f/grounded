from .SFM import SFM
from ...DataObject import Image, Mire3D, PointCloud

import Metashape as ms
import os


class Metashape(SFM):

    def __init__(self):
        self.doc = ms.Document()  # création d'un projet
        self.chunk = self.doc.addChunk()  # ajout d'un chunk dans lequel nous allons travailler

    def detection_points_homologues(self, chemin_dossier_avant: str, chemin_dossier_apres: str):
        photos = [os.path.join(chemin_dossier_avant, image_name) for image_name in os.listdir(chemin_dossier_avant)]
        photos += [os.path.join(chemin_dossier_apres, image_name) for image_name in os.listdir(chemin_dossier_apres)]
        self.chunk.addPhotos(photos)
        self.chunk.matchPhotos()

    def calibration(self):
        self.chunk.alignCameras()

    def generer_nuages_de_points(self) -> tuple[PointCloud, PointCloud]:
        pass

    def calculer_coordinates_3d_mires(self, image: Image) -> list[Mire3D]:
        pass

    def get_config(self) -> str:
        pass
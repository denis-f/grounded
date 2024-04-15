from Tools.SFM import SFM
from Tools.DetecteurMire import DetecteurMire
from Tools.TraiteurNuage3D import TraiteurNuage3D


class DensityAnalyser:

    def __init__(self, sfm: SFM, detecteur_mire: DetecteurMire, point_cloud_processor: TraiteurNuage3D):
        self.sfm = sfm
        self.detecteur_mire = detecteur_mire
        self.point_cloud_processor = point_cloud_processor

    def analyse_volume(self, photo_path_before_excavation: str, photo_path_after_excavation: str):

        # ---------------------------------------- Premier Bloc --------------------------------------------------------

        self.sfm.detection_points_homologues(photo_path_before_excavation, photo_path_after_excavation)
        self.sfm.calibration()
        point_cloud_before_excavation, point_cloud_after_excavation = self.sfm.generer_nuages_de_points()

        # --------------------------------------- Deuxième Bloc --------------------------------------------------------

        # on récupère les images ainsi que les coordonnées de leurs mires
        images = self.detecteur_mire.detection_mires(photo_path_before_excavation)
        images += self.detecteur_mire.detection_mires(photo_path_after_excavation)





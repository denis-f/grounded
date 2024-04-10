from abc import ABC, abstractmethod


class OutilPhotogrammatrique(ABC):

    @abstractmethod
    def generer_nuages_de_points(self, photos_avant: list, photo_apres: list):
        pass

    @abstractmethod
    def calculer_coordonnees_3d(self, coordonnees_2d: tuple[float, float]):
        pass

    @abstractmethod
    def detection_points_homologues(self, chemin_dossier_entree: str, chemin_dossier_sortie: str):
        pass

    @abstractmethod
    def calculer_surface(self, ):
        pass

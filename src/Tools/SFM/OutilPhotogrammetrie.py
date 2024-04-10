from abc import ABC, abstractmethod


class OutilPhotogrammatrique(ABC):

    @abstractmethod
    def generer_nuages_de_points(self, photos_avant: list, photo_apres: list):
        pass

    @abstractmethod
    def calculer_surface(self, ):
        pass

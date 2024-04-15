from abc import ABC, abstractmethod
from Grounded.DataObject import Image


class DetecteurMire(ABC):

    @abstractmethod
    def detection_mires(self, chemin_dossier_image) -> list[Image]:
        pass

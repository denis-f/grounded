from abc import ABC, abstractmethod
from Grounded.DataObject import Image


class DetecteurMire(ABC):
    """
        Interface pour les différents outils permettant la detection de mires.

        Les méthodes abstraites définies ici doivent être implémentées par toutes les classes
        non abstraites héritant de cette interface.
        """

    @abstractmethod
    def detection_mires(self, chemin_dossier_image) -> list[Image]:
        """
        Détecte chacune des mires présentes sur une image, renvoyant une liste d'objet image contenant les mires
        (Mire2D) qui apparaissent sur cette image.

        Args:
            chemin_dossier_image: un dossier contenant une ou plusieurs images en paramètre.

        Returns:
            list[Image]: une liste contenant toutes les images ayant été trouvé par le détecteur de mire
        """
        pass

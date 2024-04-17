from .Mire import Mire


class Mire2D(Mire):
    def __init__(self, identifier: int, coordinates: tuple[float, float]):
        """
        Constructeur d'un object Mire2D

        Parameters :
            identifier (int) : entier représentant l'identifiant d'une Mire
            coordinates (tuple[float, float]) : coordonnées x, y de la mire sur le plan 2D
        """
        super().__init__(identifier)
        self.coordinates: tuple[float, float] = coordinates

    def __str__(self):
        """
        Renvoie une représentation d'une Mire2D au format texte

        Returns :
            str : un string contenant les informations de la mire2D
        """
        return f"Mir( identifier: {self.identifier}, coordinates : {self.coordinates} )"

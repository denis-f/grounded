from .Mire import Mire


class Mire3D(Mire):
    def __init__(self, identifier: int, coordinates: tuple[float, float, float]):
        """
        Constructeur d'un objet Mire3D.

        Args:
            identifier (int): Entier représentant l'identifiant d'une Mire.
            coordinates (tuple[float, float, float]): Coordonnées x, y, z de la mire sur le plan 3D.
        """
        super().__init__(identifier)
        self.coordinates: tuple[float, float, float] = coordinates

    def __str__(self):
        """
        Renvoie une représentation d'une Mire3D au format texte.

        Returns:
            str: Une chaîne de caractères contenant les informations de la mire3D.
        """
        return f"Mir( identifier: {self.identifier}, coordinates : {self.coordinates} )"

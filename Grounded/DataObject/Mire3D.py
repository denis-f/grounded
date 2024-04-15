from .Mire import Mire


class Mire3D(Mire):
    def __init__(self, identifiant: int, coordonnees: tuple[float, float, float]):
        super().__init__(identifiant)
        self.coordonnees: tuple[float, float, float] = coordonnees

    def __str__(self):
        return f"Mir( identifiant: {self.identifiant}, coordonnees : {self.coordonnees} )"

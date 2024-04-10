class Mir:
    def __init__(self, identifiant: int, coordonnees: tuple[float, float]):
        self.identifiant: int = identifiant
        self.coordonnees: tuple[float, float] = coordonnees

    def __str__(self):
        return f"Mir( identifiant: {self.identifiant}, coordonnees : {self.coordonnees} )"
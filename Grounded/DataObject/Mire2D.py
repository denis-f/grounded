from .Mire import Mire


class Mire2D(Mire):
    def __init__(self, identifier: int, coordinates: tuple[float, float]):
        super().__init__(identifier)
        self.coordinates: tuple[float, float] = coordinates

    def __str__(self):
        return f"Mir( identifier: {self.identifier}, coordinates : {self.coordinates} )"

import Mir


class Image:
    def __init__(self, nom_image: str, chemin_image: str, mirs_visibles: list[Mir]):
        self.nom_image: str = nom_image
        self.chemin_image: str = chemin_image
        self.mirs_visibles: list[Mir] = mirs_visibles

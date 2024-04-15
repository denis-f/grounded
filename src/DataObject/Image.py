from .Mire2D import Mire2D
from .File import File


class Image(File):
    def __init__(self, path: str, mires_visibles: list[Mire2D]):
        super().__init__(path)
        self.mires_visibles: list[Mire2D] = mires_visibles

    def get_string_coordonnees_mires(self):
        coordonnees = ""
        for i in range(len(self.mires_visibles)):
            mir_courante = self.mires_visibles[i]
            coordonnees += f"{mir_courante.coordonnees[0]} {mir_courante.coordonnees[1]}"
            if i != len(self.mires_visibles) - 1:
                coordonnees += '\n'

        return coordonnees

    def get_nom_image_sans_extension(self):
        return self.name.split(".")[0]

    def __str__(self):
        affichage_mir = "\n"
        for mir in self.mires_visibles:
            affichage_mir += "\t\t" + mir.__str__() + "\n"

        return f"Image( \tnom: {self.name},\n \tchemin: \"{self.path}\",\n \tmirs visibles: [{affichage_mir}\t]\n)"

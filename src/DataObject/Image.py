from .Mire import Mire
from .File import File


class Image(File):
    def __init__(self, path: str, mires_visibles: list[Mire]):
        super().__init__(path)
        self.mires_visibles: list[Mire] = mires_visibles

    def supprimer_mires_uniques(self):
        mir_to_remove = []
        i = 0
        while i < len(self.mires_visibles):
            mir_courant = self.mires_visibles[i]
            # s'il n'est pas pair ou si le mir suivant n'est pas sa paire
            if mir_courant.identifiant % 2 != 0 or (i != len(self.mires_visibles) - 1
                                                    and self.mires_visibles[
                                                        i + 1].identifiant != mir_courant.identifiant + 1):
                mir_to_remove.append(mir_courant)
                i += 1
            else:
                i += 2

        for mir in mir_to_remove:  # suppression des mires isolées
            self.mires_visibles.remove(mir)

    def get_string_coordonnees_mirs(self):
        coordonnees = ""
        for i in range(len(self.mires_visibles)):
            mir_courante = self.mires_visibles[i]
            coordonnees += f"{mir_courante.coordonnees[0]} {mir_courante.coordonnees[1]}"
            if i != len(self.mires_visibles)-1:
                coordonnees += '\n'

        return coordonnees

    def get_nom_image_sans_extension(self):
        return self.name.split(".")[0]

    def __str__(self):
        affichage_mir = "\n"
        for mir in self.mires_visibles:
            affichage_mir += "\t\t" + mir.__str__() + "\n"

        return f"Image( \tnom: {self.name},\n \tchemin: \"{self.path}\",\n \tmirs visibles: [{affichage_mir}\t]\n)"

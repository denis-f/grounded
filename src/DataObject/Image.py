from .Mir import Mir


class Image:
    def __init__(self, nom: str, chemin: str, mirs_visibles: list[Mir]):
        self.nom: str = nom
        self.chemin: str = chemin
        self.mirs_visibles: list[Mir] = mirs_visibles

    def supprimer_mir_unique(self):
        mir_to_remove = []
        i = 0
        while i < len(self.mirs_visibles):
            mir_courant = self.mirs_visibles[i]
            if mir_courant.identifiant % 2 != 0 or (i != len(self.mirs_visibles) - 1
                                                    and self.mirs_visibles[
                                                        i + 1].identifiant != mir_courant.identifiant + 1):  # si il n'est pas pair ou si le mir suivant n'est pas sa pair
                mir_to_remove.append(mir_courant)
                i += 1
            else:
                i += 2

        for mir in mir_to_remove:  # suppression des mir isolés
            self.mirs_visibles.remove(mir)

    def __str__(self):
        affichage_mir = "\n"
        for mir in self.mirs_visibles:
            affichage_mir += "\t\t" + mir.__str__() + "\n"

        return f"Image( \tnom: {self.nom},\n \tchemin: \"{self.chemin}\",\n \tmirs visibles: [{affichage_mir}\t]\n)"

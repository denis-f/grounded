from .Mire2D import Mire2D
from .File import File


class Image(File):
    def __init__(self, path: str, mires_visibles: list[Mire2D]):
        """
        Constructeur d'un objet Image.

        Args:
            path (str): Le chemin menant à l'image.
            mires_visibles (list[Mire2D]): La liste des mires visibles dans l'image.
        """
        super().__init__(path)
        self.mires_visibles: list[Mire2D] = mires_visibles

    def get_string_coordinates_mires(self):
        """
        Retourne une chaîne de caractères contenant à chaque ligne les coordonnées séparées par un espace d'une mire
        contenu dans la variable mires_visibles.

        Exemple du format :
            x1 y1
            x2 y2
            x3 y3

        Returns:
            str: Une chaîne de caractères contenant les coordonnées des mires.
        """
        coordinates = ""
        for i in range(len(self.mires_visibles)):
            mir_courante = self.mires_visibles[i]
            coordinates += f"{mir_courante.coordinates[0]} {mir_courante.coordinates[1]}"
            if i != len(self.mires_visibles) - 1:
                coordinates += '\n'

        return coordinates

    def __str__(self):
        """
        Renvoie une représentation d'une image au format texte.

        Returns:
            str: Une chaîne de caractères contenant les informations de l'image.
        """
        affichage_mir = "\n"
        for mir in self.mires_visibles:
            affichage_mir += "\t\t" + mir.__str__() + "\n"

        return f"Image( \tnom: {self.name},\n \tchemin: \"{self.path}\",\n \tmirs visibles: [{affichage_mir}\t]\n)"

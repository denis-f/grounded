import os


class File:

    def __init__(self, path: str):
        """
        Constructeur d'un objet File qui permet d'accéder aux différentes informations
        d'un fichier.

        Args:
            path (str): Le chemin menant au fichier.
        """
        self.path = path
        self.name = path.split(os.sep)[-1]
        self.extension = self.name.split('.')[-1] if '.' in self.name else ''

    def get_name_without_extension(self):
        """
        Retourne le nom du fichier sans son extension.

        Returns:
            str: Le nom du fichier sans extension.
        """
        return os.path.splitext(self.name)[0]

    def get_path_directory(self):
        """
        Retourne le chemin menant au dossier contenant le fichier.

        Returns:
            str: Un chemin vers un dossier.
        """
        return os.sep.join(self.path.split(os.sep)[:-1])

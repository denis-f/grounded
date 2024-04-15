import os


class File:

    def __init__(self, path: str):
        """
            Constructeur d'un object File qui permet d'accéder aux différentes informations
            d'un fichier

            Parameters :
            path (str) : chemin absolu menant au fichier.
        """
        self.path = path
        self.name = path.split(os.sep)[-1]
        self.extension = self.name.split('.')[-1] if '.' in self.name else ''

    def get_name_without_extension(self):
        return os.path.splitext(self.name)[0]

    def get_path_directory(self):
        return os.sep.join(self.path.split(os.sep)[:-1])

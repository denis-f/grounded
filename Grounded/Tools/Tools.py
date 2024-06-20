import os
import shutil
from abc import ABC, abstractmethod

import subprocess as sb
import Grounded.logger as logger
import logging
from Grounded.utils import find_next_name_file


def read_subprocess_output(process):
    full_output = b""
    while True:
        output = process.stdout.readline()
        if output == b"" and process.poll() is not None:
            return full_output.decode()
        if output:
            full_output += output
            print(output.decode().strip())


class Tools(ABC):

    def __init__(self, working_directory: str, output_dir: str):
        """
        Constructeur commun à tous les modules de l'application grounded

        Args:
            working_directory: répertoire de travail
            output_dir: répertoire de sortie
        """
        self.working_directory = os.path.abspath(os.path.join(output_dir, working_directory))

    @staticmethod
    def subprocess(arguments: list, out_file: str):
        """
        Application d'un subprocess avec gestion automatique du log des sorties standard et d'erreur en fonction
        de la verbosité

        Args:
            arguments (list): commande à utiliser sous forme de liste dont le séprateur est les espaces de la chaine
            de caractère
            out_file (str): le nom du fichier de log devant être généré. S'il existe déjà, un un fichier avec un
            compteur sera créé

        Returns: process, str

        """
        process = sb.Popen(arguments, stdout=sb.PIPE, stderr=sb.STDOUT)
        log = logger.get_logger()
        if log.level <= logging.DEBUG:
            output = read_subprocess_output(process)
            with open(find_next_name_file(out_file), 'w+') as file:
                file.write(output)
        else:
            output = process.communicate()[0].decode()

        return process, output

    def clean(self):
        """
        Méthode permettant de supprimer le répertoire de travail du module
        """
        shutil.rmtree(self.working_directory)

    def set_up_working_space(self):
        """
        Méthode mettant en place le répertoire de travail
        """
        if os.path.exists(self.working_directory):
            self.clean()
        os.makedirs(self.working_directory, exist_ok=True)  # création du dossier de l'espace de travail

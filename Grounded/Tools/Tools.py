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

    @staticmethod
    def subprocess(arguments: list, out_file: str):
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
        shutil.rmtree(self.get_working_directory())

    def set_up_working_space(self):
        if os.path.exists(self.get_working_directory()):
            self.clean()
        os.makedirs(self.get_working_directory(), exist_ok=True)  # création du dossier de l'espace de travail

    @abstractmethod
    def get_working_directory(self):
        pass

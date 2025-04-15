import logging
import os
from Grounded.utils import path_exist

logger_name = "grounded"

def config_logger(verbosity=logging.ERROR, log_file=os.path.join(os.curdir, 'grounded.log')):
    """
    Configure le logger de l'application grounded

    Args:
        verbosity: un entier compris dans l'intervalle [0, 1]
        log_file: le nom du fichier de sortie des logs

    """
    if path_exist(log_file):
        os.remove(log_file)

    level = [logging.WARNING, logging.INFO, logging.DEBUG][verbosity]
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    # Configuration du format du logger
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.handlers.clear()
    # Création d'un handler de console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Création d'un handler de fichier
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Configurer le niveau de log des modules tiers pour qu'ils n'affichent pas leurs messages DEBUG
    logging.getLogger('matplotlib').setLevel(logging.WARNING)


def get_logger():
    """
    Retourne le logger de l'application grounded

    Returns:
        logger
    """
    return logging.getLogger(logger_name)


def get_verbosity():
    """
    Retourne le niveau de verbosité du logger de grounded

    Returns:
        level
    """
    return logging.getLogger(logger_name).level

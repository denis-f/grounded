#!/usr/bin/env python3

from Grounded.DensityAnalyser import DensityAnalyser
from Grounded.Tools import ContainerIOC
from Grounded.ScaleBarLoader import ScaleBarLoader
from Grounded.DataObject import File

import argparse
import os.path
from typing import List, Optional


def config_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Grounded est un logiciel permettant l\'analyse '
                                                 'de la densité apparente du sol par photogrammétrie')

    # Paramètre de verbosité
    parser.add_argument('-v', '--verbosity', type=int, choices=[0, 1, 2],
                        default=1, help="Paramètre de verbosité  de l'application")

    # Option de sortie
    parser.add_argument('-o', '--output',
                        type=str, help='Nom du répertoire de sortie.')

    # Option SFM
    parser.add_argument('-SFM', '-sfm',
                        type=str, help='SFM choisi pour l\'éxecution')

    parser.add_argument('-SFM_arg', '-sfm_arg',
                        type=str, help='arguments du SFM', action='append')

    # Option PointCloudProcessor
    parser.add_argument('-CloudProcessor', '-cloudprocessor',
                        type=str, help='PointCloudProcessor choisi pour l\'éxecution')

    parser.add_argument('-CloudProcessor_arg', '-cloudprocessor_arg',
                        type=str, help='arguments du PointCloudProcessor',
                        action='append')

    # Option DetecteurMire
    parser.add_argument('-Detector', '-detector',
                        type=str, help='DetecteurMire choisi pour l\'éxecution')

    parser.add_argument('-Detector_arg', '-detector_arg',
                        type=str, help='arguments du DetecteurMire',
                        action='append')

    # Option scalebar
    parser.add_argument('-scalebar',
                        type=str, help='fichier contenant les informations des scales bar')

    # Ajouter la balise -display_padding
    parser.add_argument('-display_padding', action='store_true', help="Affiche le padding utilisé pour la "
                                                                      "détection des trous dans la sortie graphique")

    # Argument positionnel pour le fichier avant
    parser.add_argument('directory_before_excavation', type=str,
                        help='Chemin du dossier contenant les photos avant excavation')

    # Argument positionnel pour le fichier après
    parser.add_argument('directory_after_excavation', type=str,
                        help='Chemin du dossier contenant les photos après excavation')

    return parser


def main():
    file_dir = File(os.path.abspath(__file__)).get_path_directory()
    parser = config_parser()
    container = ContainerIOC(os.path.join(file_dir, "Configuration", "config.yml"))
    container.set("root", file_dir)
    arguments = parser.parse_args()

    # vérification de la validité des arguments
    arguments_cheker(arguments)

    # Changement du dossier de sortie par défaut dans le conteneur si celui si est renseigné
    if arguments.output is not None:
        container.set("default_outdir_name", arguments.output)

    # On récupère le dossier de sortie
    output_dir = container.get("default_outdir_name")

    # Récupération des paramètres des tools
    sfm_kwargs = parse_arguments_parameters(arguments.SFM_arg)
    point_cloud_processor_kwargs = parse_arguments_parameters(arguments.CloudProcessor_arg)
    detecteur_mire_kwargs = parse_arguments_parameters(arguments.Detector_arg)

    # Récupération des noms des tools utilisés
    sfm_name = if_is_not_none(arguments.SFM, container.get("default_sfm"))
    point_cloud_processor_name = if_is_not_none(arguments.CloudProcessor, container.get("default_cloud_processor"))
    detecteur_mire_name = if_is_not_none(arguments.Detector, container.get("default_detector"))

    # Instanciation des tools via le conteneur ioc
    sfm = container.get(sfm_name, **sfm_kwargs)
    point_cloud_processor = container.get(point_cloud_processor_name, **point_cloud_processor_kwargs)
    detecteur_mire = container.get(detecteur_mire_name, **detecteur_mire_kwargs)

    analyser = DensityAnalyser(sfm, detecteur_mire, point_cloud_processor)

    display_config(analyser)

    # chargement des scales bars
    scale_bars = ScaleBarLoader.load(if_is_not_none(arguments.scalebar, container.get('default_scalebars_conf')))

    volumes_trous = analyser.analyse(arguments.directory_before_excavation,
                                     arguments.directory_after_excavation, scale_bars,
                                     arguments.display_padding, output_dir, arguments.verbosity)

    # Affichage des résultats
    print("###########################################################################\n"
          "############################# Fin d'exécution #############################\n"
          "###########################################################################\n\n")
    for i in range(len(volumes_trous)):
        print(f"volume du trou n°{i + 1} : {volumes_trous[i]}")


def arguments_cheker(arguments):
    if arguments.directory_before_excavation is None:
        raise argparse.ArgumentError(None, "image directory before excavation is missing")
    if arguments.directory_after_excavation is None:
        raise argparse.ArgumentError(None, "image directory after excavation is missing")
    if not os.path.exists(arguments.directory_before_excavation):
        raise argparse.ArgumentError(None, "image directory before excavation does not exists")
    if not os.path.exists(arguments.directory_after_excavation):
        raise argparse.ArgumentError(None, "image directory after excavation does not exists")


def if_is_not_none(argument, default):
    return argument if argument is not None else default


def parse_arguments_parameters(arguments: Optional[List]) -> dict:
    kwargs = {}
    if arguments is None:
        return kwargs

    for arg in arguments:
        decomposed_arg = arg.split('=')
        if len(decomposed_arg) != 2:
            raise SyntaxError("bad arguments format")

        kwargs[decomposed_arg[0]] = decomposed_arg[1]

    return kwargs


def display_config(analyser):
    print("\033[34mConfiguration d'exécution :\n")
    print(f"{analyser.get_config()}\n\033[0m")


if __name__ == '__main__':
    main()

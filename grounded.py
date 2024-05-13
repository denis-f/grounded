import os.path

from Grounded.DensityAnalyser import DensityAnalyser
from Grounded.Tools import ContainerIOC
from Grounded.ScaleBarLoader import ScaleBarLoader
from Grounded.DataObject import File

import argparse
from typing import List, Optional


def config_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Grounded est un logiciel permettant l\'analyse '
                                                 'de la densité apparente du sol par photogrammétrie')

    # Option SFM
    parser.add_argument('-SFM', '-sfm',
                        metavar='SFM', type=str, help='SFM choisi pour l\'éxecution')

    parser.add_argument('-SFM_arg', '-sfm_arg',
                        metavar='SFM arguments', type=str, help='arguments du SFM', action='append')

    # Option PointCloudProcessor
    parser.add_argument('-CloudProcessor', '-cloudprocessor',
                        metavar='CloudProcessor', type=str, help='PointCloudProcessor choisi pour l\'éxecution')

    parser.add_argument('-CloudProcessor_arg', '-cloudprocessor_arg',
                        metavar='CloudProcessor arguments', type=str, help='arguments du PointCloudProcessor',
                        action='append')

    # Option DetecteurMire
    parser.add_argument('-Detector', '-detector',
                        metavar='DetecteurMire', type=str, help='DetecteurMire choisi pour l\'éxecution')

    parser.add_argument('-Detector_arg', '-detector_arg',
                        metavar='Detector arguments', type=str, help='arguments du DetecteurMire',
                        action='append')

    # Option scalebar
    parser.add_argument('-scalebar',
                        metavar='scalebar_file', type=str, help='fichier contenant les informations des scales bar')

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
    arguments = parser.parse_args()

    # vérification de la validité des arguments
    arguments_cheker(arguments)

    # Récupération des paramètres des tools
    sfm_kwargs = parse_arguments_parameters(arguments.SFM_arg)
    point_cloud_processor_kwargs = parse_arguments_parameters(arguments.CloudProcessor_arg)
    detecteur_mire_kwargs = parse_arguments_parameters(arguments.Detector_arg)

    # Récupération des noms des tools utilisés
    sfm_name = if_is_not_none(arguments.SFM, "micmac")
    point_cloud_processor_name = if_is_not_none(arguments.CloudProcessor, "cloudcompare")
    detecteur_mire_name = if_is_not_none(arguments.Detector, "detection_cctag")

    # Instanciation des tools via le conteneur ioc
    sfm = container.get(sfm_name, kwargs_dict=sfm_kwargs)
    point_cloud_processor = container.get(point_cloud_processor_name, kwargs_dict=point_cloud_processor_kwargs)
    detecteur_mire = container.get(detecteur_mire_name, kwargs_dict=detecteur_mire_kwargs)

    analyser = DensityAnalyser(sfm, detecteur_mire, point_cloud_processor)

    # chargement des scales bars
    scale_bars = ScaleBarLoader.load(if_is_not_none(arguments.scalebar, os.path.join(file_dir, "Configuration",
                                                                                     "scaleBar.csv")))

    volumes_trous = analyser.analyse(arguments.directory_before_excavation,
                                     arguments.directory_after_excavation, scale_bars)

    # Affichage des résultats
    print("###########################################################################\n"
          "############################# Fin d'exécution #############################\n"
          "###########################################################################\n\n")
    for i in range(len(volumes_trous)):
        print(f"volume du trou n°{i + 1} : {volumes_trous[i]}")


def arguments_cheker(arguments):
    if arguments.directory_before_excavation is None:
        raise argparse.ArgumentError("directory_before_excavation", "missing image file")
    if arguments.directory_after_excavation is None:
        raise argparse.ArgumentError("directory_after_excavation", "missing image file")


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


if __name__ == '__main__':
    main()

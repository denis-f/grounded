import numpy as np

from Tools.SFM import SFM
from Tools.DetecteurMire import DetecteurMire
from Tools.TraiteurNuage3D import TraiteurNuage3D
from DataObject import PointCloud, Mire3D, Mire

import statistics


def calculate_average_mire_3d(mires_3d: list[Mire3D]) -> list[Mire3D]:
    dictionnaire_coordonnees_mires = {}
    for mire in mires_3d:
        if mire.identifiant not in dictionnaire_coordonnees_mires:
            dictionnaire_coordonnees_mires[mire.identifiant] = {'x': [], 'y': [], 'z': []}
        dictionnaire_coordonnees_mires[mire.identifiant]['x'].append(mire.coordonnees[0])
        dictionnaire_coordonnees_mires[mire.identifiant]['y'].append(mire.coordonnees[1])
        dictionnaire_coordonnees_mires[mire.identifiant]['z'].append(mire.coordonnees[2])

    mires_3d_moyens: list[Mire3D] = []
    for identifiant in dictionnaire_coordonnees_mires.keys():
        moyenne_x = statistics.mean(dictionnaire_coordonnees_mires[identifiant]['x'])
        moyenne_y = statistics.mean(dictionnaire_coordonnees_mires[identifiant]['y'])
        moyenne_z = statistics.mean(dictionnaire_coordonnees_mires[identifiant]['z'])

        mires_3d_moyens.append(Mire3D(identifiant, (moyenne_x, moyenne_y, moyenne_z)))

    return mires_3d_moyens


def calculate_standard_deviation_mire_3d(mires_3d: list[Mire3D]):
    dictionnaire_coordonnees_mires = {}
    for mire in mires_3d:
        if mire.identifiant not in dictionnaire_coordonnees_mires:
            dictionnaire_coordonnees_mires[mire.identifiant] = {'x': [], 'y': [], 'z': []}
        dictionnaire_coordonnees_mires[mire.identifiant]['x'].append(mire.coordonnees[0])
        dictionnaire_coordonnees_mires[mire.identifiant]['y'].append(mire.coordonnees[1])
        dictionnaire_coordonnees_mires[mire.identifiant]['z'].append(mire.coordonnees[2])

    ecart_type = {}
    for identifiant in dictionnaire_coordonnees_mires.keys():
        ecart_type_x = statistics.stdev(dictionnaire_coordonnees_mires[identifiant]['x'])
        ecart_type_y = statistics.stdev(dictionnaire_coordonnees_mires[identifiant]['y'])
        ecart_type_z = statistics.stdev(dictionnaire_coordonnees_mires[identifiant]['z'])

        ecart_type[identifiant] = {'x': ecart_type_x, 'y': ecart_type_y, 'z': ecart_type_z}

    return ecart_type


def delete_mire_without_pair(mires: list[Mire]):
    mires.sort(key=lambda x: x.identifiant)
    mire_to_remove = []
    i = 0
    while i < len(mires):
        mire_courant = mires[i]
        # s'il n'est pas pair ou si le mir suivant n'est pas sa paire
        if mire_courant.identifiant % 2 != 0 or (i != len(mires) - 1
                                                 and mires[i + 1].identifiant != mire_courant.identifiant + 1):
            mire_to_remove.append(mire_courant)
            i += 1
        else:
            i += 2

    for mire in mire_to_remove:  # suppression des mires isolées
        mires.remove(mire)


def distance_euclidienne(point1, point2):
    """
    Calcule la distance euclidienne entre deux points dans un espace multidimensionnel.

    Args:
        point1 (list, tuple, numpy.ndarray): Coordonnées du premier point.
        point2 (list, tuple, numpy.ndarray): Coordonnées du deuxième point.

    Returns:
        float: La distance euclidienne entre les deux points.
    """
    point1 = np.array(point1)
    point2 = np.array(point2)
    return np.sqrt(np.sum((point1 - point2) ** 2))


def calculate_average_scale_factor(mires: list[Mire3D], reglet_size):
    scale_factors: list[float] = []
    for i in range(0, len(mires), 2):
        scale_factors.append(reglet_size / distance_euclidienne(mires[i].coordonnees, mires[i + 1].coordonnees))

    return statistics.mean(scale_factors)


class DensityAnalyser:

    def __init__(self, sfm: SFM, detecteur_mire: DetecteurMire, point_cloud_processor: TraiteurNuage3D):
        self.sfm = sfm
        self.detecteur_mire = detecteur_mire
        self.point_cloud_processor = point_cloud_processor

    def analyse_volume(self, photo_path_before_excavation: str, photo_path_after_excavation: str, reglet_size=0.22):
        # ---------------------------------------- Premier Bloc --------------------------------------------------------

        self.sfm.detection_points_homologues(photo_path_before_excavation, photo_path_after_excavation)
        self.sfm.calibration()
        point_cloud_before_excavation, point_cloud_after_excavation = self.sfm.generer_nuages_de_points()

        # --------------------------------------- Deuxième Bloc --------------------------------------------------------

        # on récupère les images ainsi que les coordonnées 2D de leurs mires
        images = self.detecteur_mire.detection_mires(photo_path_before_excavation)
        images += self.detecteur_mire.detection_mires(photo_path_after_excavation)

        # on récupère les coordonnées 3d de chacune des mires stockées dans les images
        mires_3d: list[Mire3D] = []
        for image in images:
            mires_3d += self.sfm.calculer_coordonnees_3d_mires(image)

        # on calcule les coordonnées moyennes de chaque mire 3d ainsi que l'écart type
        mires_3d_moyens = calculate_average_mire_3d(mires_3d)
        ecart_type = calculate_standard_deviation_mire_3d(mires_3d)

        # on supprime les mires isolés dont la paire n'a pas pu être détecté
        delete_mire_without_pair(mires_3d_moyens)

        # on calcule le facteur d'échelle moyen
        mean_scale_factor = calculate_average_scale_factor(mires_3d_moyens, reglet_size)

        # on redimensionne les nuages de points à l'aide de ce facteur d'échelle
        point_cloud_before_excavation = self.point_cloud_processor.mise_a_echelle(point_cloud_before_excavation,
                                                                                  mean_scale_factor)

        point_cloud_after_excavation = self.point_cloud_processor.mise_a_echelle(point_cloud_after_excavation,
                                                                                 mean_scale_factor)

        # -------------------------------------- Troisième Bloc --------------------------------------------------------
        print("fin d'éxecution")

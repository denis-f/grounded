import os

import numpy as np

from Grounded.Tools.SFM import SFM
from Grounded.Tools.DetecteurMire import DetecteurMire
from Grounded.Tools.PointCloudProcessor import PointCloudProcessor
from Grounded.DataObject import PointCloud, Mire3D, Mire, Raster

import statistics
import rasterio
from math import pi
from rasterio.crs import CRS
from scipy.ndimage import generic_filter
from shapely.geometry import shape, Polygon
from shapely import polygonize
from scipy.ndimage import label
from shapely import buffer
from skimage import measure
from rasterio.plot import show
import matplotlib


def calculate_average_mire_3d(mires_3d: list[Mire3D]) -> list[Mire3D]:
    dictionnaire_coordinates_mires = {}
    for mire in mires_3d:
        if mire.identifier not in dictionnaire_coordinates_mires:
            dictionnaire_coordinates_mires[mire.identifier] = {'x': [], 'y': [], 'z': []}
        dictionnaire_coordinates_mires[mire.identifier]['x'].append(mire.coordinates[0])
        dictionnaire_coordinates_mires[mire.identifier]['y'].append(mire.coordinates[1])
        dictionnaire_coordinates_mires[mire.identifier]['z'].append(mire.coordinates[2])

    mires_3d_moyens: list[Mire3D] = []
    for identifier in dictionnaire_coordinates_mires.keys():
        moyenne_x = statistics.mean(dictionnaire_coordinates_mires[identifier]['x'])
        moyenne_y = statistics.mean(dictionnaire_coordinates_mires[identifier]['y'])
        moyenne_z = statistics.mean(dictionnaire_coordinates_mires[identifier]['z'])

        mires_3d_moyens.append(Mire3D(identifier, (moyenne_x, moyenne_y, moyenne_z)))

    return mires_3d_moyens


def calculate_standard_deviation_mire_3d(mires_3d: list[Mire3D]):
    dictionnaire_coordinates_mires = {}
    for mire in mires_3d:
        if mire.identifier not in dictionnaire_coordinates_mires:
            dictionnaire_coordinates_mires[mire.identifier] = {'x': [], 'y': [], 'z': []}
        dictionnaire_coordinates_mires[mire.identifier]['x'].append(mire.coordinates[0])
        dictionnaire_coordinates_mires[mire.identifier]['y'].append(mire.coordinates[1])
        dictionnaire_coordinates_mires[mire.identifier]['z'].append(mire.coordinates[2])

    ecart_type = {}
    for identifier in dictionnaire_coordinates_mires.keys():
        ecart_type_x = statistics.stdev(dictionnaire_coordinates_mires[identifier]['x'])
        ecart_type_y = statistics.stdev(dictionnaire_coordinates_mires[identifier]['y'])
        ecart_type_z = statistics.stdev(dictionnaire_coordinates_mires[identifier]['z'])

        ecart_type[identifier] = {'x': ecart_type_x, 'y': ecart_type_y, 'z': ecart_type_z}

    return ecart_type


def delete_mire_without_pair(mires: list[Mire]):
    mires.sort(key=lambda x: x.identifier)
    mire_to_remove = []
    i = 0
    while i < len(mires):
        mire_courant = mires[i]
        # s'il n'est pas pair ou si le mir suivant n'est pas sa paire
        if mire_courant.identifier % 2 != 0 or (i != len(mires) - 1
                                                and mires[i + 1].identifier != mire_courant.identifier + 1):
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
        scale_factors.append(reglet_size / distance_euclidienne(mires[i].coordinates, mires[i + 1].coordinates))

    return statistics.mean(scale_factors)


def mean(x):
    # Exclure les valeurs NA du calcul de la moyenne
    valid_values = x[~np.isnan(x)]
    if len(valid_values) > 0:
        return np.mean(valid_values)
    else:
        return np.nan


def prospect_zone(raster: Raster):
    with rasterio.open(raster.path, "r+") as data_set:
        raster_array = data_set.read(2)
    return generic_filter(raster_array, mean, size=(25, 25))


def delimitate_holes(raster_zone, tol_simplify=0.01, width_buffer=0.02, area_hole=0.008, thres_hole=0.00021,
                     k_cox_threshold=0.35, minimal_hole_area=0.004):
    """
    Identifie et délimite les trous (zones non-continues) dans un raster.

    Args:
        raster_zone (numpy.ndarray): Raster représentant la zone d'intérêt.
        tol_simplify (float): Tolérance de simplification des polygones.
        width_buffer (float): Largeur d'agrandissement des polygones.
        area_hole (float): Surface minimale requise pour un trou.
        thres_hole (float): Seuil de binarisation du raster.
        k_cox_threshold (float): Seuil de rondeur (Cox) pour filtrer les polygones.
        minimal_hole_area (float): Surface minimale supplémentaire pour filtrer les polygones (optionnel).

    Returns:
        list: Liste de polygones Shapely représentant les trous délimités, triés de gauche à droite.
    """

    # Fonction pour calculer la rondeur selon la formule de Cox
    def roundness(polygone: Polygon):
        return 4 * np.pi * polygone.area / (polygone.length ** 2)

    def find_polygons(mask):
        # Trouver les contours dans le masque
        contours = measure.find_contours(mask, fully_connected='high')

        all_points = np.concatenate(contours)

        # Créer un polygone à partir de tous les points des contours
        polygon = Polygon(all_points)

        return polygon

    # Binarisation du raster avec le seuil
    mask_zone = raster_zone > thres_hole

    # Identification des groupes de cellules connectées (trous)
    labeled_image, num_labels = label(mask_zone.astype(int))

    # Estimation de la surface des groupes (trous)
    hole_areas = []
    raster_size = mask_zone.shape[0] * mask_zone.shape[1]
    for lab in range(1, num_labels + 1):
        hole_cells = labeled_image == lab
        # ici la surface d'un trou est égal à son ratio par rapport à la taille de l'image
        hole_area = np.sum(hole_cells) / raster_size
        hole_areas.append((lab, hole_area))

    # Sélection des groupes correspondant aux trous potentiels (surface >= area_hole)
    potential_holes = [lab for lab, area in hole_areas if area >= area_hole]

    polygons = []
    # Process the features
    for lab in potential_holes:
        polygons.append(find_polygons(np.where(labeled_image == lab, 1, 0)))

    # Simplification des polygones
    simplified_polygons = [polygon.simplify(tolerance=tol_simplify, preserve_topology=True) for polygon in polygons]

    # Filtrage des polygones par rondeur (Cox) et surface minimale
    filtered_polygons = []
    for polygon in simplified_polygons:
        a = roundness(polygon)
        if roundness(polygon) >= k_cox_threshold:
            filtered_polygons.append(polygon)

    # Agrandissement des polygones
    buffered_polygons = [buffer(polygon, distance=width_buffer) for polygon in filtered_polygons]

    # Tri des polygones de gauche à droite
    sorted_polygons = sorted(buffered_polygons, key=lambda poly: poly.bounds[0])

    return sorted_polygons


def polygon_coordinate_conversion(raster: Raster, polygon: Polygon) -> list[tuple[float, float]]:
    data_set = rasterio.open(raster.path, 'r')
    a = data_set.transform
    coordinates = []
    for point in polygon.exterior.coords:
        x, y = data_set.xy(point[0], point[1])
        coordinates.append((x, y))

    data_set.close()
    return coordinates


class DensityAnalyser:
    """
    Classe permettant l'analyse de la densité apparente du sol en utilisant la photogrammétrie. Une implémentation
    des techniques démontrés dans ces articles:

    "Joining multi-epoch archival aerial images in a single SfM block allows 3-D change detection with almost
    exclusively image information." - D. Feurer, F. Vinatier

    "Assessing new sensor-based volume measurement methods for high-throughput bulk density estimation in the field
    under various soil conditions." - Guillaume Coulouma, Denis Feurer, Fabrice Vinatier, Olivier Huttel
    """

    def __init__(self, sfm: SFM, detecteur_mire: DetecteurMire, point_cloud_processor: PointCloudProcessor):
        """
        Initialise une instance de la classe DensityAnalyser
        Args:
            sfm: un objet implémentant l'interface SFM
            detecteur_mire: un objet implémentant l'interface DetecteurMire
            point_cloud_processor: un objet implémentant l'interface PointCloudProcessor
        """
        self.sfm = sfm
        self.detecteur_mire = detecteur_mire
        self.point_cloud_processor = point_cloud_processor

    def analyse(self, photo_path_before_excavation: str, photo_path_after_excavation: str, reglet_size=0.22):
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
            mires_3d += self.sfm.calculer_coordinates_3d_mires(image)

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

        # on calcule le raster de la distance entre les deux nuages de points
        raster = self.point_cloud_processor.cloud_to_cloud_distance(point_cloud_before_excavation,
                                                                    point_cloud_after_excavation)

        # on isole et on homogénéise la bande que nous allons étudier
        zone_tot = prospect_zone(raster)

        # on récupère les polygones détourant les trous
        holes_polygons = delimitate_holes(zone_tot, 0.01, 0.02, 0.008, 0.005, 0.55, 0.004)

        # on récupère les coordonnées des points des polygones dans l'espace du raster
        list_holes_coordinates = [polygon_coordinate_conversion(raster, hole) for hole in holes_polygons]

        # on récupère les trous détourés
        holes_cropped: list[tuple[PointCloud, PointCloud]] = []
        for hole_coordinates in list_holes_coordinates:
            before = self.point_cloud_processor.crop_point_cloud(point_cloud_before_excavation, hole_coordinates)
            after = self.point_cloud_processor.crop_point_cloud(point_cloud_after_excavation, hole_coordinates)
            holes_cropped.append((before, after))

        # on récupère les volumes des différents trous triés de gauche à droite et de haut en bas
        holes_volumes = [self.point_cloud_processor.volume_between_clouds(hole[0], hole[1]) for hole in holes_cropped]

        with open("results.txt", 'w') as file:
            file.write(f"nombre de trou détectés : {len(holes_volumes)}\n"
                       "------------Trous triés de gauche à droite------------")
            for i in range(len(holes_volumes)):
                file.write(f"volume du trou n°{i + 1} : {holes_volumes[i]}")

        return holes_volumes

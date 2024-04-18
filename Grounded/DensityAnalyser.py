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
from rasterio.features import shapes
from shapely.geometry import shape, Polygon
from shapely.ops import unary_union


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


def prospect_zone(raster: Raster):
    with rasterio.open(raster.path, "r+") as src:
        src.crs = crs = CRS.from_epsg(32632)  # Définir le système de coordonnées EPSG 32632 (UTM Zone 32N)
        raster_array = src.read(1)

    return generic_filter(raster_array, lambda x: np.mean(x), size=(25, 25))


def roundness(polygon):
    perimeter = polygon.length
    area = polygon.area
    return 4 * pi * area / (perimeter ** 2)


def delimitateHoles(path_clouds, rasterZone, tol_simplify=0.01, width_buffer=0.02, area_hole=0.008, thres_hole=0.005,
                    K_Cox_threshold=0.35, minimal_hole_area=0.004):
    with rasterio.open(path_clouds, "r+") as src:
        # Thresholding the smoothed raster to identify the hole
        mask_zone = (rasterZone > thres_hole).astype('uint8')

        # Vectorization of the hole contour
        results = list(
            (geom, value)
            for geom, value in shapes(mask_zone, mask=mask_zone, transform=src.transform)
        )

        polygons = [shape(geom) for geom, value in results]
        for geom, value in results:
            print(geom)
            print(geom)
        maxV = [value for geom, value in results if len(np.array(geom['coordinates']).flatten()) * src.res[0] * src.res[1] > area_hole]

        # Identification of hole contour that reached a minimal area (multiple holes)
        hole_contours = [polygons[i] for i, value in enumerate(maxV)]

        # Reduction of stairs in the polygon
        simplified_hole_contours = [hole.simplify(tol_simplify) for hole in hole_contours]

        # Discarding "non-round" polygons
        round_holes = [hole for hole in simplified_hole_contours if roundness(hole) > K_Cox_threshold]

        # Filtering by minimal hole area
        filtered_holes = [hole for hole in round_holes if hole.area > minimal_hole_area]

        # Enlargement of polygon area
        buffered_holes = [hole.buffer(width_buffer) for hole in filtered_holes]

        # Reordering the multiple polygons from left to right
        ordered_holes = sorted(buffered_holes, key=lambda hole: hole.bounds[0])

        return unary_union(ordered_holes)


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
        self.sfm.calibration("FraserBasic")
        point_cloud_before_excavation, point_cloud_after_excavation = self.sfm.generer_nuages_de_points("MicMac")

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
        # TODO avec Denis concernant la partie technique

    def test(self):
        point_cloud_before_excavation = PointCloud(
            "cloudCompare_working_directory/avant_0.ply")
        point_cloud_after_excavation = PointCloud(
            "cloudCompare_working_directory/apres_1.ply")
        # on récupère le raster correspondant à la difference entre
        raster = Raster("cloudCompare_working_directory/raster.tif")

        # on calcule la zone de prospection
        zone_tot = prospect_zone(raster)
        holes_sel = delimitateHoles(raster.path, zone_tot, 0.01, 0.02, 0.002, 0.005, 0.6)
        print(holes_sel)

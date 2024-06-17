from Grounded.Tools.SFM import SFM
from Grounded.Tools.DetecteurMire import DetecteurMire
from Grounded.Tools.PointCloudProcessor import PointCloudProcessor
from Grounded.Tools.SFM.SFM import SFM
from Grounded.DataObject import PointCloud, Mire3D, Mire, Raster, ScaleBar, Mire2D, Image

import statistics
import rasterio
import numpy as np
from scipy.ndimage import generic_filter
from shapely.geometry import Polygon
from scipy.ndimage import label
from shapely import buffer
from skimage import measure
from matplotlib import pyplot, patches
from matplotlib.colors import LinearSegmentedColormap


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
        ecart_type_x = statistics.stdev(dictionnaire_coordinates_mires[identifier]['x']) \
            if len(dictionnaire_coordinates_mires[identifier]['x']) > 1 \
            else 0

        ecart_type_y = statistics.stdev(dictionnaire_coordinates_mires[identifier]['y']) \
            if len(dictionnaire_coordinates_mires[identifier]['y']) > 1 \
            else 0

        ecart_type_z = statistics.stdev(dictionnaire_coordinates_mires[identifier]['z']) \
            if len(dictionnaire_coordinates_mires[identifier]['z']) > 1 \
            else 0

        ecart_type[identifier] = {'x': ecart_type_x, 'y': ecart_type_y, 'z': ecart_type_z}

    return ecart_type


def scale_bars_filter_without_pair(mires: list[Mire], scale_bars: list[ScaleBar]) -> list[ScaleBar]:
    mires.sort(key=lambda x: x.identifier)
    scale_bars_copy = scale_bars.copy()
    for scale_bar in scale_bars:
        try:
            start_mire = [mire for mire in mires if mire.identifier == scale_bar.start.identifier][0]
            end_mire = [mire for mire in mires if mire.identifier == scale_bar.end.identifier][0]
        except IndexError:
            mires = [mire for mire in mires if mire.identifier != scale_bar.start.identifier and
                     mire.identifier != scale_bar.end.identifier]
            scale_bars_copy.remove(scale_bar)

    return scale_bars_copy


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


def calculate_average_scale_factor(mires: list[Mire3D], scale_bars):
    scale_factors: list[float] = []
    for scale_bar in scale_bars:
        start_mire = [mire for mire in mires if mire.identifier == scale_bar.start.identifier][0]
        end_mire = [mire for mire in mires if mire.identifier == scale_bar.end.identifier][0]
        scale_factors.append(scale_bar.length / distance_euclidienne(start_mire.coordinates, end_mire.coordinates))

    return statistics.mean(scale_factors)


def prospect_zone(raster: Raster):
    def mean(x):
        # Exclure les valeurs NA du calcul de la moyenne
        valid_values = x[~np.isnan(x)]
        if len(valid_values) > 0:
            return np.mean(valid_values)
        else:
            return np.nan

    with rasterio.open(raster.path, "r+") as data_set:
        raster_array = data_set.read(2)
    return generic_filter(raster_array, mean, size=(25, 25))


def get_coordinates_mires3d_in_raster(mires3d: list[Mire3D], raster: Raster, scale_factor: float):
    coords = []
    for mire in mires3d:
        x, y, z = mire.coordinates

        # Convertir les coordonnées spatiales (x, y) en indices de pixel (row, col)
        x, y = raster.xy_3d_space_to_xy_raster(x * scale_factor, y * scale_factor)
        coords.append((x, y))

    return coords


def delimitate_holes(raster_resolution: float, raster_zone, tol_simplify=0.01, width_buffer=0.02, area_hole=0.008,
                     thres_hole=0.00021, k_cox_threshold=0.35, coords_mires_in_raster=[],
                     min_height: float = 0, max_height: float = 0, min_width: float = 0, max_width: float = 0):
    """
    Identifie et délimite les trous (zones non-continues) dans un raster.

    Args:
        coords_mires_in_raster:
        raster (Raster): Dataobject Raster stockant les informations sur le fichier
        raster_zone (numpy.ndarray): matrice représentant la zone d'intérêt.
        tol_simplify (float): Tolérance de simplification des polygones.
        width_buffer (float): Largeur d'agrandissement des polygones.
        area_hole (float): Surface minimale requise pour un trou.
        thres_hole (float): Seuil de binarisation du raster.
        k_cox_threshold (float): Seuil de rondeur (Cox) pour filtrer les polygones.
        width_padding (float): Pourcentage de padding en largeur appliqué à la détection des trous
        height_padding (float): Pourcentage de padding en hauteur appliqué à la détection des trous

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
    for lab in range(1, num_labels + 1):
        hole_cells = labeled_image == lab
        # ici la surface d'un trou est égal à son ratio par rapport à la taille de l'image
        hole_area = np.sum(hole_cells) * (raster_resolution ** 2)
        hole_areas.append((lab, hole_area))

    # Sélection des groupes correspondant aux trous potentiels (surface >= area_hole)
    biggers_holes = [lab for lab, area in hole_areas if area >= area_hole]

    polygons = []
    # Process the features
    for lab in biggers_holes:
        polygons.append(find_polygons(np.where(labeled_image == lab, 1, 0)))

    # Ici on vérifie si les polygones sont centrés
    centred_polygons = []

    for poly in polygons:
        if min_height <= poly.centroid.x <= max_height and min_width <= poly.centroid.y <= max_width:
            centred_polygons.append(poly)

    # Simplification des polygones
    simplified_polygons = [polygon.simplify(tolerance=tol_simplify) for polygon in centred_polygons]

    # Filtrage des polygones par rondeur (Cox) et surface minimale
    filtered_polygons = []
    for polygon in simplified_polygons:
        if roundness(polygon) >= k_cox_threshold:
            filtered_polygons.append(polygon)

    # Agrandissement des polygones
    buffered_polygons = [buffer(polygon, distance=width_buffer / raster_resolution) for polygon in filtered_polygons]

    # Tri des polygones de gauche à droite
    sorted_polygons = sorted(buffered_polygons, key=lambda poly: poly.centroid.y)

    return sorted_polygons


def polygon_coordinate_conversion(raster: Raster, polygon: Polygon) -> list[tuple[float, float]]:
    coordinates = []
    for point in polygon.exterior.coords:
        # On convertit les coordonnées dans la matrice en coordonnées dans le raster
        x, y = raster.xy(point[0], point[1])
        coordinates.append((x, y))

    return coordinates


def save_plot_result(raster_array, holes_polygons, list_volumes, output_name, display_padding, mires_coords,
                     min_height, max_height, min_width, max_width):
    # On récupère les valeurs maximales et minimales
    mini = np.nanmin(raster_array)
    maxi = np.nanmax(raster_array)

    # On définit l'échelle de couleur qui sera utilisé pour l'affichage des du plot
    colors = [(0, '#aaffff'), (0.04, '#001f6f'), (0.1, '#00f600'), (0.15, '#035700'), (0.25, '#fcfd00'),
              (0.6, '#ef0000'), (0.8, '#921a1a'), (1, '#e7e6e6')]
    high_contrast = LinearSegmentedColormap.from_list('high_contrast', colors)

    # Ajout du plot du raster ainsi que de la barre de couleur
    pyplot.imshow(raster_array, cmap=high_contrast, vmin=mini, vmax=maxi)
    pyplot.colorbar()

    # Ajout du rectangle correspondant à la zone de détection des trous
    if display_padding:
        x = min_height
        y = min_width
        width = max_width - min_width
        height = max_height - min_height
        rect = patches.Rectangle((y, x), height=height, width=width, linewidth=1, edgecolor='r', facecolor='none')
        pyplot.gca().add_patch(rect)

        x = [coord[0] for coord in mires_coords]
        y = [coord[1] for coord in mires_coords]
        pyplot.scatter(x, y, color='blue', s=10, marker='o')

    # Ajout des informations concernant les trous
    for i in range(len(holes_polygons)):
        poly = holes_polygons[i]

        # Affichage des polygons sur l'image
        x_coords, y_coords = poly.exterior.xy  # Extraire les coordonnées x et y du polygone
        x_coords = list(x_coords)
        y_coords = list(y_coords)
        pyplot.plot(y_coords, x_coords, color='black')

        # Ajout des volumes
        pyplot.text(poly.centroid.y, poly.centroid.x, format(list_volumes[i], '.6f'),
                    fontsize=5, ha='center', va='center', color='black')

    # Enregistrement au format .pdf du fichier
    pyplot.savefig(output_name, format='pdf')


class BadModuleError(Exception):
    def __init__(self, module_name):
        self.module_name = module_name
        self.message = f"Le module de type '{self.module_name}' est incorrect"
        super().__init__(self.message)


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
        if not isinstance(sfm, SFM): raise BadModuleError("sfm")
        if not isinstance(detecteur_mire, DetecteurMire): raise BadModuleError("detecteur de mire")
        if not isinstance(point_cloud_processor, PointCloudProcessor): raise BadModuleError("point cloud processor")

        self.sfm = sfm
        self.detecteur_mire = detecteur_mire
        self.point_cloud_processor = point_cloud_processor

    def analyse(self, photo_path_before_excavation: str, photo_path_after_excavation: str, scale_bars: list[ScaleBar],
                display_padding: bool = False):

        # Détection des mires présentes sur les images
        images = self._mire_detection(photo_path_before_excavation, photo_path_after_excavation)

        # Vérification de la configuration des scalebars afin de détecter une potentielle erreur de l'utilisateur
        detected_target_are_in_loaded_scalebar = self._check_scalebars_settings(images, scale_bars)

        # Génération des nuages de points à l'aide du module sfm
        point_cloud_before_excavation, point_cloud_after_excavation = self._generate_point_cloud(
            photo_path_before_excavation,
            photo_path_after_excavation)

        # Calcul de la position des mires dans l'espace 3D
        mires_3d, ecart_type = self._calculate_mire3d(images)

        # Suppression des ScaleBars dont au moins l'une des extrémités est manquante
        scale_bars = scale_bars_filter_without_pair(mires_3d, scale_bars)

        # on calcule le facteur de redimmensionnement por mettre à l'echelle les nuages de points
        scale_factor = calculate_average_scale_factor(mires_3d, scale_bars)

        print("Redimensionnement des nuages de points en cours...")
        point_cloud_before_excavation = self._resize_point_clouds(point_cloud_before_excavation, scale_factor)
        point_cloud_after_excavation = self._resize_point_clouds(point_cloud_after_excavation, scale_factor)

        # -------------------------------------- Calcul du volume des trous  -------------------------------------------
        print("Calcul du volume en cours...")
        # on calcule le raster de la distance entre les deux nuages de points
        raster = self._cloud_to_cloud_distance(point_cloud_before_excavation, point_cloud_after_excavation)

        # on isole et on homogénéise la bande que nous allons étudier
        zone_tot = prospect_zone(raster)

        resolution = raster.resolution

        coords_mires_in_raster = get_coordinates_mires3d_in_raster(mires_3d, raster, scale_factor)
        min_width, max_width, min_height, max_height = self._calculate_detection_zone(resolution,
                                                                                      coords_mires_in_raster)

        # on récupère les polygones détourant les trous
        holes_polygons = delimitate_holes(resolution, zone_tot, 0.01, 0.02, 0.007, 0.005, 0.4, coords_mires_in_raster,
                                          min_height, max_height, min_width, max_width)

        # on récupère les coordonnées des points des polygones dans l'espace du raster
        list_holes_coordinates = [polygon_coordinate_conversion(raster, hole) for hole in holes_polygons]

        # on récupère les trous détourés
        holes_cropped: list[tuple[PointCloud, PointCloud]] = []
        for hole_coordinates in list_holes_coordinates:
            before = self.point_cloud_processor.crop_point_cloud(point_cloud_before_excavation, hole_coordinates)
            after = self.point_cloud_processor.crop_point_cloud(point_cloud_after_excavation, hole_coordinates)
            holes_cropped.append((before, after))

        # on récupère les volumes des différents trous triés
        holes_volumes = [self.point_cloud_processor.volume_between_clouds(hole[0], hole[1]) for hole in holes_cropped]

        # ##############################################################################################################
        # ###################################### Enregistrement des résultats ##########################################
        # ##############################################################################################################

        # on enregistre au format txt les résultats
        with open("results.txt", 'w') as file:
            file.write(f"nombre de trous détectés : {len(holes_volumes)}\n"
                       "------------Trous triés de gauche à droite------------\n")
            for i in range(len(holes_volumes)):
                file.write(f"volume du trou n°{i + 1} : {holes_volumes[i]}\n")

        # on enregistre au format pdf les résultats
        save_plot_result(zone_tot, holes_polygons, holes_volumes, "results.pdf",
                         display_padding, coords_mires_in_raster, min_height, max_height, min_width, max_width)

        with open("config.txt", 'w') as file:
            file.write(f"{self.sfm.get_config()}\n"
                       f"{self.point_cloud_processor.get_config()}\n"
                       f"{self.detecteur_mire.get_config()}")

        return holes_volumes

    def _mire_detection(self, photo_path_before_excavation: str, photo_path_after_excavation: str) -> list[Image]:
        print("Détection des mires présentes sur les images...")
        # on récupère les images ainsi que les coordonnées 2D de leurs mires
        images = self.detecteur_mire.detection_mires(photo_path_before_excavation)
        images += self.detecteur_mire.detection_mires(photo_path_after_excavation)
        return images

    @staticmethod
    def _check_scalebars_settings(images: list[Image], scale_bars: list[ScaleBar]):
        # vérification du paramétrage des scalebar
        id_scalebars = []
        for scalebar in scale_bars:
            id_scalebars.append(scalebar.end.identifier)
            id_scalebars.append(scalebar.start.identifier)
        detected_target_are_in_loaded_scalebar = True
        # on boucle sur les mires détectées, chaque mire détectée doit etre dans les scalebar
        for im in images:
            for mir in im.mires_visibles:
                if mir.identifier not in id_scalebars:
                    detected_target_are_in_loaded_scalebar = False
                    print("\033[31mWARNING /!\ La mire " + str(
                        mir.identifier) + " détectée dans l'image " + im.name + " n'est pas dans les scalebars. Vérifier le fichier chargé.\033[0m")

        return detected_target_are_in_loaded_scalebar

    def _generate_point_cloud(self, photo_path_before_excavation, photo_path_after_excavation):
        print("Début du calcul des nuages de points.")
        return self.sfm.generer_nuages_de_points(photo_path_before_excavation, photo_path_after_excavation)

    def _calculate_mire3d(self, images: list[Image]) -> (list[Mire3D], dict[int, float]):
        mires_3d: list[Mire3D] = []
        for image in images:
            mires_3d += self.sfm.calculer_coordinates_3d_mires(image)

        # on calcule les coordonnées moyennes de chaque mire 3d ainsi que l'écart type
        mires_3d_moyens = calculate_average_mire_3d(mires_3d)
        ecart_type = calculate_standard_deviation_mire_3d(mires_3d)

        return mires_3d_moyens, ecart_type

    def _resize_point_clouds(self, point_cloud: PointCloud, scale_factor: float):
        # on redimensionne les nuages de points à l'aide de ce facteur d'échelle
        resize_point_cloud = self.point_cloud_processor.mise_a_echelle(point_cloud, scale_factor)

        return resize_point_cloud

    def _cloud_to_cloud_distance(self, point_cloud_ref: PointCloud, point_cloud_compared: PointCloud) -> Raster:
        return self.point_cloud_processor.cloud_to_cloud_distance(point_cloud_ref, point_cloud_compared)

    @staticmethod
    def _calculate_detection_zone(resolution, coords_mires_in_raster):
        min_width = min(x for x, y in coords_mires_in_raster)
        max_width = max(x for x, y in coords_mires_in_raster)
        min_height = min(y for x, y in coords_mires_in_raster)
        max_height = max(y for x, y in coords_mires_in_raster)

        y_mean = statistics.mean([y for x, y in coords_mires_in_raster])

        # Ajout de la marge en bas pour détecter les trous qui dépassent
        if abs(min_height - y_mean) < abs(max_height - y_mean):
            max_height += (0.1 / resolution)
        else:
            min_height += (0.1 / resolution)

        return min_width, max_width, min_height, max_height

import logging
import os.path
import shutil
import subprocess

from Grounded.Tools.SFM import SFM
from Grounded.Tools.DetecteurMire import DetecteurMire
from Grounded.Tools.PointCloudProcessor import PointCloudProcessor
from Grounded.Tools.SFM.SFM import SFM
from Grounded.DataObject import PointCloud, Mire3D, Mire, Raster, ScaleBar, Mire2D, Image, File
import Grounded.logger as logger
from Grounded.utils import raise_logged

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
import trimesh

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

    def __init__(self, sfm: SFM, detecteur_mire: DetecteurMire, point_cloud_processor: PointCloudProcessor,
                 output_dir: str = os.curdir, verbosity: int = 1):
        """
        Initialise une instance de la classe DensityAnalyser
        Args:
            sfm: un objet implémentant l'interface SFM
            detecteur_mire: un objet implémentant l'interface DetecteurMire
            point_cloud_processor: un objet implémentant l'interface PointCloudProcessor
            output_dir (str): dossier de sortie
            verbosity (int): un entier compris dans l'intervalle [0;2]
        """
        # Configuration des logs
        logger.config_logger(verbosity, os.path.join(output_dir, "grounded.log"))
        log = logger.get_logger()
        if not isinstance(sfm, SFM): raise_logged(log.critical, BadModuleError("sfm"))
        if not isinstance(detecteur_mire, DetecteurMire): raise_logged(log.critical, BadModuleError("detecteur de mire"))
        if not isinstance(point_cloud_processor, PointCloudProcessor): raise_logged(log.critical, BadModuleError("point cloud processor"))

        self.sfm = sfm
        self.detecteur_mire = detecteur_mire
        self.point_cloud_processor = point_cloud_processor
        self.output_dir = output_dir
        if shutil.which("git"):
            self.git_revision = subprocess.run(['git', '-C', File(__file__).get_path_directory(),
                                                'rev-parse', 'HEAD'], stdout=subprocess.PIPE,
                                               stderr=subprocess.PIPE, text=True).stdout.strip()
        else:
            self.git_revision = None

    def analyse(self, photo_path_before_excavation: str, photo_path_after_excavation: str, scale_bars: list[ScaleBar],
                display_padding: bool = False) -> list[float]:
        """

        Args:
            photo_path_before_excavation (str): chemin vers le fichier avant excavation
            photo_path_after_excavation (str): chemin vers le fichier après excavation
            scale_bars (list[ScaleBar]): réglets utilisés
            display_padding (bool): Option d'affiche de la zone de détection sur la sortie graphique

        Returns:
            list[float]: volumes des trous trouvés
        """

        photo_path_before_excavation = os.path.abspath(photo_path_before_excavation)
        photo_path_after_excavation = os.path.abspath(photo_path_after_excavation)

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

        # Vérification de la valeur de l'écart des écarts types
        self._check_ecart_type(ecart_type, 0.1)

        # Suppression des ScaleBars dont au moins l'une des extrémités est manquante
        scale_bars = scale_bars_filter_without_pair(mires_3d, scale_bars)

        # on calcule le facteur de redimmensionnement por mettre à l'echelle les nuages de points
        scale_factor = calculate_average_scale_factor(mires_3d, scale_bars)

        # Rotation des nuages de points pour être perpendiculaire au plan moyen des mires
        mires_3d, point_cloud_before_excavation, point_cloud_after_excavation = self._rotate_2point_clouds_and_3Dtargets(
            point_cloud_before_excavation, point_cloud_after_excavation, mires_3d
        )
        with open(os.path.join(self.output_dir, "scaleFactor.txt"), 'w') as file:
            file.write(f"facteur d'échelle : {scale_factor}")

        print(f"Redimensionnement des nuages de points en cours... (facteur d'échelle : {scale_factor})")
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
        with open(os.path.join(self.output_dir, "results.txt"), 'w') as file:
            file.write(f"nombre de trous détectés : {len(holes_volumes)}\n"
                       "------------Trous triés de gauche à droite------------\n")
            for i in range(len(holes_volumes)):
                file.write(f"volume du trou n°{i + 1} : {holes_volumes[i]}\n")

        # on enregistre au format pdf les résultats
        save_plot_result(zone_tot, holes_polygons, holes_volumes, os.path.join(self.output_dir, "results.pdf"),
                         display_padding, coords_mires_in_raster, min_height, max_height, min_width, max_width)

        with open(os.path.join(self.output_dir, "config.txt"), 'w') as file:
            file.write(self.get_config())

        if logger.get_verbosity() >= logging.WARN:
            self._clean()

        return holes_volumes

    def get_config(self):
        result = f"git-revision : {self.git_revision}\n" \
                 f"SFM : {self.sfm.get_config()}\n" \
                 f"PointCloudProcessor : {self.point_cloud_processor.get_config()}\n" \
                 f"DetecteurMire : {self.detecteur_mire.get_config()}\n"

        return result

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
                    logger.get_logger().warn(f"/!\\ La mire {mir.identifier} détectée dans l'image "
                                             f"{im.name} n'est pas dans les scalebars. Vérifier le fichier chargé.")

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

    def _fit_plane(self, x, y, z):
        # Solution de Ben trouvée sur StackOverFlow https://stackoverflow.com/a/44315488
        tmp_A = []
        tmp_b = []
        for i in range(len(x)):
            tmp_A.append([x[i], y[i], 1])
            tmp_b.append(z[i])
        b = np.matrix(tmp_b).T
        A = np.matrix(tmp_A)
        fit = (A.T * A).I * A.T * b
        errors = b - A * fit
        residual = np.linalg.norm(errors)
        return fit[0, 0], fit[1, 0], fit[2, 0], errors, residual

    def _rotate_points_to_abc_plane(self, points, a, b, c):
        # Ensure points is a numpy array
        points = np.array(points)

        # Normal vector of the plane
        normal = np.array([-a, -b, 1])
        normal = normal / np.linalg.norm(normal)

        # Calculate rotation axis (cross product of normal and [0, 0, 1])
        rotation_axis = np.cross(normal, [0, 0, 1])
        rotation_axis = rotation_axis / np.linalg.norm(rotation_axis)

        # Calculate rotation angle
        cos_theta = np.dot(normal, [0, 0, 1])
        # sin_theta = np.linalg.norm(rotation_axis)
        sin_theta = np.sqrt(1 - cos_theta ** 2)

        # Construct rotation matrix using Rodriguez rotation formula
        K = np.array([[0, -rotation_axis[2], rotation_axis[1]],
                      [rotation_axis[2], 0, -rotation_axis[0]],
                      [-rotation_axis[1], rotation_axis[0], 0]])
        R = np.eye(3) + sin_theta * K + (1 - cos_theta) * np.dot(K, K)

        # Apply rotation to all points
        rotated_points = np.dot(points, R.T)

        return rotated_points

    def _apply_two_rotations_to_one_point_cloud(self, point_cloud: PointCloud, a, b, c, rotmat):
        # on charge le premier nuage
        PTS = trimesh.load(point_cloud.path)
        # on le clone
        PTS_rotated = PTS
        # on change les points du nuage de point par la rotation des points du nuage initial pour que le Z fasse face au plan d'équation ax + by + c = z
        PTS_rotated.vertices = self._rotate_points_to_abc_plane(PTS.vertices, a, b, c)
        # on fait la rotation autour de Z pour avoir l'endroit où il y a le moins de mires en bas (= les réglets du haut en haut)
        x1, y1 = np.dot(rotmat,PTS_rotated.vertices[:,0:2].T)
        #on met à jour les coordonnées x, y du nuage de point
        PTS_rotated.vertices[:,0:2] = np.array([x1,y1]).T
        # on crée un nouveau nom de fichier en ajoutant _Rotated au nuage de base
        path_point_cloud = os.sep.join(
            [point_cloud.get_path_directory(), point_cloud.get_name_without_extension() + '_Rotated.ply'])
        out_file = open(path_point_cloud, 'wb')
        out_file.write(trimesh.exchange.ply.export_ply(PTS_rotated))
        out_file.close()

        return PointCloud(path_point_cloud)

    def _rotate_2point_clouds_and_3Dtargets(self, point_cloud1: PointCloud, point_cloud2: PointCloud, mires_3d: Mire3D):

        # Get 3D coordinates of mires_3d
        x = [mire.coordinates[0] for mire in mires_3d]
        y = [mire.coordinates[1] for mire in mires_3d]
        z = [mire.coordinates[2] for mire in mires_3d]
        # fit a plane to these 3D points
        a, b, c, errors, residual = self._fit_plane(x, y, z)
        # compute the result of the rotation of the mires_3d (x,y,z)
        res = self._rotate_points_to_abc_plane(np.array([x, y, z]).T, a, b, c)
        # mise à jour des coordonnées des mires
        rotated_mires_3d = mires_3d
        xr = x
        yr = y
        for i in np.arange(len(mires_3d)):
            rotated_mires_3d[i].coordinates = res[i,:]
            xr[i] = rotated_mires_3d[i].coordinates[0]
            yr[i] = rotated_mires_3d[i].coordinates[1]

        # at this point we get a,b,c the plane fitted to initial position of the mires_3d and rotated_mires_3d
        # we need to rotate point clouds around the Z axis so that les mires horizontales soient en haut et les mires verticales soient verticales
        # # on postule que le "bas" est défini par l'endroit où il n'y a pas de réglet
        # #   => c'est raccord avec la config en vertical/fosse =  le bas est le côté où est le bac de prélévèement
        # #   => c'est raccord avec la config en horizontal/par-dessus = le "bas" est le côté où se situe l'opérateur qui prélève, on laisse un côté sans mire pour simplifier
        # # dans ce cas de figure le barycentre des mires sera tiré du côté opposé où il n'y a pas de mire.
        # # on calcule le barycentre des mires avec la médiane (moins sensible aux extrèmes) => point H (np.median(xr) , np.median(yr))
        # # on calcule le point milieu du rectangle englobant => point O, box_centre
        # # => la verticale orientée vers le haut est définie par le vecteur OH
        box_centre_xr, box_centre_yr = (np.min(xr) + np.max(xr)) / 2, (np.min(yr) + np.max(yr)) / 2
        # l'angle de la rotation pour passer d'un vecteur (xr,yr) à un vecteur (0,1) c'est arctan (xr/yr) on fait donc arctan2(xr,yr)
        # voir arctan2 https://numpy.org/doc/2.1/reference/generated/numpy.arctan2.html#numpy.arctan2
        angle = np.arctan2 ( (np.median(xr)-box_centre_xr), (np.median(yr)-box_centre_yr) )
        rotmat = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])

        ## APPLICATION
        # MIRES 3D
        #on calcule les nouvelles coordonnées x,y
        xr2,yr2 = np.dot(rotmat, [xr, yr])
        # on met à jour les mires déjà tournées dans le plan
        for i in np.arange(len(rotated_mires_3d)):
            rotated_mires_3d[i].coordinates[0] = xr2[i]
            rotated_mires_3d[i].coordinates[1] = yr2[i]

        # NUAGES DE POINTS
        #fonction qui fait les deux rotation sur un fichier ply


        point_cloud1 = self._apply_two_rotations_to_one_point_cloud(point_cloud1, a, b, c, rotmat)
        point_cloud2 = self._apply_two_rotations_to_one_point_cloud(point_cloud2, a, b, c, rotmat)
        # PTS_1 = trimesh.load(point_cloud2.path)
        # PTS_1_rotated = PTS_1
        # PTS_1_rotated.vertices = self._rotate_points_to_abc_plane(PTS_1.vertices, a, b, c)
        # x2, y2 = np.dot(rotmat, PTS_1_rotated.vertices[0:2])
        # PTS_1_rotated.vertices[0:2] = [x2, y2]
        # out_file = open(point_cloud2.path, 'wb')
        # out_file.write(trimesh.exchange.ply.export_ply(PTS_1_rotated))
        # out_file.close()


        return rotated_mires_3d, point_cloud1, point_cloud2

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

    @staticmethod
    def _check_ecart_type(ecart_type: dict, threshold=0.1):
        for key, values in ecart_type.items():
            if values.get('x') >= threshold or values.get('y') >= threshold or values.get('z') >= threshold:
                logger.get_logger().warn(
                    f"L'écart type des coordonnées de la mire {key} est anormalement élevé {values}")

    def _clean(self):
        self.sfm.clean()
        self.detecteur_mire.clean()
        self.point_cloud_processor.clean()

import shutil

from .SFM import SFM
from Grounded.DataObject import Image, Mire2D, Mire3D, PointCloud

import Metashape as ms
import os
import re


def add_photo_with_prefix(chunk: ms.Chunk, photos: list[str], prefix: str):
    chunk.addPhotos(photos)
    for camera in chunk.cameras:
        camera.label = f"{prefix}{camera.label}"


def copy_chunk_with_camera_with_prefix(chunk: ms.Chunk, prefix: str) -> ms.Chunk:
    copy_chunk = chunk.copy()
    camera_without_prefix = [camera for camera in copy_chunk.cameras if re.search(f"^{prefix}", camera.label) is None]
    for camera in camera_without_prefix:
        copy_chunk.remove(camera)

    return copy_chunk


def build_point_cloud(chunk: ms.Chunk, path: str, downscale: int) -> PointCloud:
    chunk.buildDepthMaps(downscale=downscale, filter_mode=ms.AggressiveFiltering)
    chunk.buildPointCloud(point_colors=True)
    chunk.exportPointCloud(path=path, format=ms.PointCloudFormatPLY, clip_to_boundary=True)
    return PointCloud(path)


def photos_coord_to_3d_coords(chunk: ms.Chunk, x: float, y: float, camera_name: str) -> tuple[float, float, float]:
    cameras = [camera for camera in chunk.cameras if
               camera.transform and camera.type == ms.Camera.Type.Regular]  # list of aligned cameras

    surface = chunk.point_cloud
    crs = chunk.crs
    transform_matrix = chunk.transform.matrix

    for camera in cameras:
        if camera.label == camera_name:
            ray_origin = camera.unproject(ms.Vector([x, y, 0]))
            ray_target = camera.unproject(ms.Vector([x, y, 1]))
            point = surface.pickPoint(ray_origin, ray_target)
            if point is not None:
                coord = crs.project(transform_matrix.mulp(point))
                return coord.x, coord.y, coord.z
            else:
                return None,None,None

    raise ValueError("Aucune camera alignée ne porte ce nom")


class Metashape(SFM):
    """
    Implémente l'interface SFM et implémente les méthodes nécessaires pour l'exécution de Metashape,
    un logiciel de photogrammétrie.

    Elle est utilisée pour effectuer diverses opérations telles que la détection de points homologues, la calibration
    de la caméra, la génération de nuages de points, et le calcul des coordonnées 3D des mires dans une image.
    """

    def __init__(self, working_directory: str, output_dir: str, downscale="8"):
        """
        Initialise une instance de la classe MicMac.

        Args:
            path_mm3d (str): Le chemin vers l'exécutable MicMac.
            distorsion_model (str): un modèle de distorsion
            zoom_final (str): un zoom final


        Returns:
            None
        """
        super().__init__(working_directory, output_dir)
        self.doc = ms.Document()  # création d'un projet
        self.chunk = self.doc.addChunk()  # ajout d'un chunk dans lequel nous allons travailler
        self.downscale = int(downscale)
        self.chunk_before = None
        self.chunk_after = None

        self.set_up_working_space()

    def _add_photos_to_chunk(self, chemin_dossier_avant: str, chemin_dossier_apres: str):
        # Ajout des photos avant excavation avec le préfixe "0_"
        photos = [os.path.join(chemin_dossier_avant, image_name) for image_name in os.listdir(chemin_dossier_avant)]
        chunk_before = self.doc.addChunk()
        add_photo_with_prefix(chunk_before, photos, "0_")

        # Ajout des photos avant excavation avec le préfixe "1_"
        photos = [os.path.join(chemin_dossier_apres, image_name) for image_name in os.listdir(chemin_dossier_apres)]
        chunk_after = self.doc.addChunk()
        add_photo_with_prefix(chunk_after, photos, "1_")

        self.doc.mergeChunks(chunk_before, chunk_after)
        self.chunk = self.doc.chunks[-1]

    def _align_images(self):
        self.chunk.matchPhotos(downscale=1, generic_preselection=True, reference_preselection=True,
                               reference_preselection_mode=ms.ReferencePreselectionSource, keypoint_limit=100000,
                               tiepoint_limit=10000, keep_keypoints=True)
        self.chunk.alignCameras()
        self.chunk.resetRegion()
        self.chunk.optimizeCameras()
        self.chunk.updateTransform()

    def generer_nuages_de_points(self, chemin_dossier_avant: str, chemin_dossier_apres: str) -> tuple[
        PointCloud, PointCloud]:
        """
        Méthode pour générer des nuages de points avant/après excavation.

        Args:
            chemin_dossier_avant (str): Le chemin vers le dossier contenant les images avant excavation.
            chemin_dossier_apres (str): Le chemin vers le dossier contenant les images après excavation.

        Returns:
            Tuple[NuageDePoints, NuageDePoints]: Un tuple contenant deux objets NuageDePoints représentant les nuages de points
            avant et après excavation.
            tuple[0] ⇛ avant et tuple[1] ⇛ après
        """
        self._add_photos_to_chunk(chemin_dossier_avant, chemin_dossier_apres)
        self._align_images()

        self.chunk_before = copy_chunk_with_camera_with_prefix(self.chunk, "0_")
        point_cloud_before = build_point_cloud(self.chunk_before,
                                               os.path.join(self.working_directory, "point_cloud_0.ply"),
                                               self.downscale)

        self.chunk_after = copy_chunk_with_camera_with_prefix(self.chunk, "1_")
        point_cloud_after = build_point_cloud(self.chunk_after,
                                              os.path.join(self.working_directory, "point_cloud_1.ply"),
                                              self.downscale)

        return point_cloud_before, point_cloud_after

    def calculer_coordinates_3d_mires(self, image: Image) -> (list[Mire2D], list[Mire3D]):
        """
        Méthode pour calculer les coordonnées 3D des cibles dans une image.

        Args:
            image (Image): un objet Image contenant des cibles

        Returns:
            List[Mire3D]: Une liste d'objets Mire3D contenant les coordonnées 3D des cibles.
        """
        if len([camera for camera in self.chunk_before.cameras
                if re.search(f"0_{image.get_name_without_extension()}", camera.label) is not None]) > 0:
            chunk = self.chunk_before
            local_name = f"0_{image.get_name_without_extension()}"
        else:
            chunk = self.chunk_after
            local_name = f"1_{image.get_name_without_extension()}"

        mires3d = []
        for mire2d in image.mires_visibles:
            x, y, z = photos_coord_to_3d_coords(chunk, mire2d.coordinates[0], mire2d.coordinates[1], local_name)
            if x is not None and y is not None and z is not None:
                mires3d.append(Mire3D(mire2d.identifier, (x, y, z)))

        return image.mires_visibles,mires3d

    def get_config(self) -> str:
        return f"Metashape(working_directory={self.working_directory}, downscale={self.downscale})"

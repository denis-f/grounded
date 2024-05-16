from .SFM import SFM
from ...DataObject import Image, Mire3D, PointCloud

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


class Metashape(SFM):

    def __init__(self):
        self.doc = ms.Document()  # création d'un projet
        self.chunk = self.doc.addChunk()  # ajout d'un chunk dans lequel nous allons travailler

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
        self._add_photos_to_chunk(chemin_dossier_avant, chemin_dossier_apres)
        self._align_images()

        chunk_before = copy_chunk_with_camera_with_prefix(self.chunk, "0_")
        chunk_before.buildDepthMaps(downscale=8, filter_mode=ms.AggressiveFiltering,)
        chunk_before.buildPointCloud(point_colors=True)
        chunk_before.exportPointCloud(path="/home/lisahcalc/Grounded/avant_cloud(2).ply",
                                      format=ms.PointCloudFormatPLY, clip_to_boundary=True)

        chunk_after = copy_chunk_with_camera_with_prefix(self.chunk, "1_")
        chunk_after.buildDepthMaps(downscale=8, filter_mode=ms.AggressiveFiltering)
        chunk_after.buildPointCloud(point_colors=True)
        chunk_after.exportPointCloud(path="/home/lisahcalc/Grounded/apres_cloud(2).ply",
                                      format=ms.PointCloudFormatPLY, clip_to_boundary=True)

    def calculer_coordinates_3d_mires(self, image: Image) -> list[Mire3D]:
        pass

    def get_config(self) -> str:
        pass

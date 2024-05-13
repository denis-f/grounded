from .DetecteurMire import DetecteurMire
import Metashape
import os
import shutil
import xml.etree.ElementTree as et

from Grounded.DataObject import Image, Mire2D


def parse_export_file(export_file_path, photos) -> list[Image]:
    tree = et.parse(export_file_path)
    chunk = tree.getroot().find("chunk")
    markers = chunk.find("markers")
    dict_id_marker_number = {marker.attrib["id"]: marker.attrib["label"].split(" ")[-1] for marker in markers}
    images = []
    cameras = chunk.find("cameras")
    markers_coord = chunk.find("frames/frame[@id='0']/markers")
    for camera in cameras:
        path = next((chemin for chemin in photos if camera.attrib["label"] == chemin.split(os.sep)[-1].split(".")[0]),
                    None)
        image = Image(path, [])
        for marker in markers_coord:
            marker_number = int(dict_id_marker_number.get(marker.attrib["marker_id"]))
            location = marker.find(f"location[@camera_id='{camera.attrib['id']}']")
            if location is not None:
                x = float(location.attrib["x"])
                y = float(location.attrib["y"])
                image.mires_visibles.append(Mire2D(marker_number, (x, y)))
        images.append(image)

    return images


class DetectionMetashape(DetecteurMire):

    def __init__(self):
        self.working_directory = "detecteur_Metashape_working_directory"
        self.set_up_working_space()

    def set_up_working_space(self):
        if os.path.exists(self.working_directory):
            shutil.rmtree(self.working_directory)
        os.makedirs(self.working_directory, exist_ok=True)  # création du dossier de l'espace de travail

    def detection_mires(self, chemin_dossier_image: str) -> list[Image]:
        doc = Metashape.Document()  # création d'un projet
        chunk = doc.addChunk()  # ajout d'un chunk dans lequel nous allons travailler

        # ajout des photos dans l'expace de travail
        photos = [os.path.join(chemin_dossier_image, image_name) for image_name in os.listdir(chemin_dossier_image)]
        chunk.addPhotos(photos)

        chunk.detectMarkers()  # lancement de la detection de mirs

        exported_file_path = os.path.join(self.working_directory,
                                          f"{chemin_dossier_image.split(os.sep)[-1]}_exportMarkers.xml")

        chunk.exportMarkers(exported_file_path)

        return parse_export_file(exported_file_path, photos)

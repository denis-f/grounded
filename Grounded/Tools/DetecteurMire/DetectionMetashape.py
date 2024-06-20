from .DetecteurMire import DetecteurMire
import Metashape
import os
import shutil
import xml.etree.ElementTree as et

from Grounded.DataObject import Image, Mire2D
from Grounded.utils import config_builer


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
    """
    Implémente l'interface DetecteurMire et implémente les méthodes nécessaires pour l'exécution de detection,
    une composante de CCTag

    Elle est utilisée pour calculer les coordonnées de chacune des mires présentes sur une image
    """

    def __init__(self, working_directory: str, output_dir: str):
        """
        Initialise une instance de la classe DetectionMetashape

        Args:
            working_directory: répertoire de travail
            output_dir: dossier de sortie
        """
        super().__init__(working_directory, output_dir)
        self.set_up_working_space()

    def detection_mires(self, chemin_dossier_image: str) -> list[Image]:
        """
        Détecte chacune des mires présentes sur une image, renvoyant une liste d'objet image contenant les mires
        (Mire2D) qui apparaissent sur cette image.

        Args:
            chemin_dossier_image: un dossier contenant une ou plusieurs images en paramètre.

        Returns:
            list[Image]: une liste contenant toutes les images ayant été trouvé par le détecteur de mire
        """
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

    def get_config(self) -> str:
        return config_builer(self, "DetectionMetashape")

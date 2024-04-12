from src.Tools.DetecteurMire.DetectionCCTag import DetectionCCTag
from src.Tools.SFM import MicMac
from src.Tools.TraiteurNuage3D import CloudCompare
from DataObject import PointCloud

#detect = DetectionCCTag()
#images = detect.detection_mires("../../02-Essaies/00_DATA")

#m = MicMac("/opt/micmac/bin/mm3d", "../../Dossier_photo_test/avant", "../../Dossier_photo_test/apres")

c = CloudCompare()

c.mise_a_echelle(PointCloud("../../02-Essaies/plyFiles/C3DC_avant.ply"), 0.08173343)
c.mise_a_echelle(PointCloud("../../02-Essaies/plyFiles/C3DC_apres.ply"), 0.08173343)

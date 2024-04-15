from src.Tools.DetecteurMire.DetectionCCTag import DetectionCCTag
from src.Tools.SFM import MicMac
from src.Tools.TraiteurNuage3D import CloudCompare
from DataObject import PointCloud
from DataObject import Image, Mire2D

#detect = DetectionCCTag()
#images = detect.detection_mires("../../02-Essaies/00_DATA")

m = MicMac("/opt/micmac/bin/mm3d")
#m.detection_points_homologues("../../Dossier_photo_test/avant", "../../Dossier_photo_test/apres")
#m.calibration()
#m.generer_nuages_de_points()
#c = CloudCompare()

#c.mise_a_echelle(PointCloud("../../02-Essaies/plyFiles/C3DC_avant.ply"), 0.08173343)
#c.mise_a_echelle(PointCloud("../../02-Essaies/plyFiles/C3DC_apres.ply"), 0.08173343)

image = Image("test/test2/DSC_0380.JPG", [Mire2D(0, (946.37, 1079.23)),
                                          Mire2D(1, (200, 20.23))])
print(m.calculer_coordonnees_3d_mires(image))

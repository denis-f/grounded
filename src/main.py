from src.DataObject import Mire
from src.Tools.DetecteurMire.DetectionCCTag import DetectionCCTag
from src.Tools.SFM import MicMac
from src.Tools.TraiteurNuage3D import CloudCompare
from DataObject import PointCloud
from DataObject import Image, Mire2D, Mire3D
from src.DensityAnalyser import DensityAnalyser


#detect = DetectionCCTag()
#images = detect.detection_mires("../../02-Essaies/00_DATA")

m = MicMac("/opt/micmac/bin/mm3d")
#m.detection_points_homologues("../../Dossier_photo_test/avant", "../../Dossier_photo_test/apres")
#m.calibration()
#m.generer_nuages_de_points()
c = CloudCompare()
d = DetectionCCTag("/opt/CCTag/")
#c.mise_a_echelle(PointCloud("../../02-Essaies/plyFiles/C3DC_avant.ply"), 0.08173343)
#c.mise_a_echelle(PointCloud("../../02-Essaies/plyFiles/C3DC_apres.ply"), 0.08173343)

analyser = DensityAnalyser(m, d, c)
analyser.analyse_volume("/home/francoin/Documents/Projet_Densite_Sol/Dossier_photo_test/avant",
                        "/home/francoin/Documents/Projet_Densite_Sol/Dossier_photo_test/apres")


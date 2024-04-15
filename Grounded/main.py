from Grounded.Tools.DetecteurMire.DetectionCCTag import DetectionCCTag
from Grounded.Tools.SFM import MicMac
from Grounded.Tools.TraiteurNuage3D import CloudCompare
from Grounded.DensityAnalyser import DensityAnalyser


m = MicMac("/opt/micmac/bin/mm3d")
c = CloudCompare()
d = DetectionCCTag("/opt/CCTag/")

analyser = DensityAnalyser(m, d, c)
analyser.analyse_volume("/home/francoin/Documents/Projet_Densite_Sol/Dossier_photo_test/avant",
                        "/home/francoin/Documents/Projet_Densite_Sol/Dossier_photo_test/apres")


from src.Tools.DetecteurMir.DetectionCCTag import DetectionCCTag
from src.Tools.SFM import MicMac

#detect = DetectionCCTag()
#images = detect.detection_mirs("../../02-Essaies/00_DATA")
#print(images)

m = MicMac("/opt/micmac/bin/mm3d", "../../Dossier_photo_test/avant", "../../Dossier_photo_test/apres")

m.detection_points_homologues()
print("detection des points homologues terminé")
m.calibration()
print("calibration terminée")
m.generer_nuages_de_points()
print("génération du nuage de points terminé")


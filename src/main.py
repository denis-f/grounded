from src.Tools.DetecteurMir.DetectionCCTag import DetectionCCTag
from src.Tools.SFM import MicMac

#detect = DetectionCCTag()
#images = detect.detection_mirs("../../02-Essaies/00_DATA")
#print(images)

m = MicMac("/opt/micmac/bin/", "../../Dossier_photo_test/avant", "../../Dossier_photo_test/apres")

m.detection_points_homologues()


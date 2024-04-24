import sys

from Grounded.DensityAnalyser import DensityAnalyser
from Grounded.Tools.DetecteurMire import DetectionCCTag
from Grounded.Tools.PointCloudProcessor import CloudCompare
from Grounded.Tools.SFM import MicMac

try:
    dossier_avant = sys.argv[1]
    dossier_apres = arg2 = sys.argv[2]
except IndexError as error:
    pass
    raise Exception("nombre d'arguments insuffisant")

print(f"le dossier contenant les photos avant excavation est : {dossier_avant}")
print(f"le dossier contenant les photos apres excavation est : {dossier_apres}")


m = MicMac("/opt/micmac/bin/mm3d", "FraserBasic", "MicMac")  # initialisation d'un SFM
c = CloudCompare("cloudcompare.CloudCompare", "2.11.1")  # initialisation de PointCloudProcessor
d = DetectionCCTag("/opt/CCTag/")  # initialisation d'un DetecteurMire

analyser = DensityAnalyser(m, d, c)
volumes_trous = analyser.analyse(dossier_avant,
                                 dossier_apres)

print("###########################################################################\n"
      "############################# Fin d'exécution #############################\n"
      "###########################################################################\n\n")
for i in range(len(volumes_trous)):
    print(f"volume du trou n°{i + 1} : {volumes_trous[i]}")

from Grounded.Tools.DetecteurMire.DetectionCCTag import DetectionCCTag
from Grounded.Tools.SFM import MicMac
from Grounded.Tools.PointCloudProcessor import CloudCompare
from Grounded.DensityAnalyser import DensityAnalyser

m = MicMac("/opt/micmac/bin/mm3d", "FraserBasic", "MicMac")  # initialisation d'un SFM
c = CloudCompare("cloudcompare.CloudCompare")  # initialisation de PointCloudProcessor
d = DetectionCCTag("/opt/CCTag/")  # initialisation d'un DetecteurMire

# instantiation d'un objet DensityAnalyser construit à partir des modules défini au-dessus
analyser = DensityAnalyser(m, d, c)

# analyse du volume des trous présents sur les photos
volumes_trous = analyser.analyse("/home/francoin/Documents/Projet_Densite_Sol/Dossier_photo_test/avant",  # à compléter par le dossier contenant les images avant excavation
                                 "/home/francoin/Documents/Projet_Densite_Sol/Dossier_photo_test/apres")  # à compléter par le dossier contenant les images après excavation

print("###########################################################################\n"
      "############################# Fin d'exécution #############################\n"
      "###########################################################################\n\n")
for i in range(len(volumes_trous)):
    print(f"volume du trou n°{i + 1} : {volumes_trous[i]}")

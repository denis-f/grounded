from Grounded.Tools.DetecteurMire.DetectionCCTag import DetectionCCTag
from Grounded.Tools.DetecteurMire.DetectionMetashape import DetectionMetashape
from Grounded.Tools.SFM import MicMac
from Grounded.Tools.PointCloudProcessor import CloudCompare
from Grounded.DensityAnalyser import DensityAnalyser
from Grounded.ScaleBarLoader import ScaleBarLoader
from Grounded.Tools.SFM.Metashape import Metashape

scale_bars = ScaleBarLoader.load("Configuration/oldScaleBar.csv")


#m = MicMac("/opt/micmac/bin/mm3d", "FraserBasic", "QuickMac")  # initialisation d'un SFM
m = Metashape(8)
c = CloudCompare("'C:\Program Files\CloudCompare\CloudCompare.exe'", "2.13.1")  # initialisation de PointCloudProcessor
d = DetectionMetashape()  # initialisation d'un DetecteurMire

# instantiation d'un objet DensityAnalyser construit à partir des modules défini au-dessus
analyser = DensityAnalyser(m, d, c)
# analyse du volume des trous présents sur les photos
volumes_trous = analyser.analyse("..\\avant", # à compléter par le dossier contenant les images avant excavation
                                 "..\\apres",  # à compléter par le dossier contenant les images après excavation
                                 scale_bars)

print("###########################################################################\n"
      "############################# Fin d'exécution #############################\n"
      "###########################################################################\n\n")
for i in range(len(volumes_trous)):
    print(f"volume du trou n°{i + 1} : {volumes_trous[i]}")




from Grounded.Tools.DetecteurMire.DetectionCCTag import DetectionCCTag
#from Grounded.Tools.DetecteurMire.DetectionMetashape import DetectionMetashape
from Grounded.Tools.SFM import MicMac
from Grounded.Tools.PointCloudProcessor import CloudCompare
from Grounded.DensityAnalyser import DensityAnalyser
from Grounded.ScaleBarLoader import ScaleBarLoader
from Grounded.Tools.SFM.Metashape import Metashape

#from Grounded.Tools.SFM.Metashape import Metashape

#scale_bars = ScaleBarLoader.load("Configuration/oldScaleBar.csv")
scale_bars = ScaleBarLoader.load("Configuration/scaleBar.csv")

output_dir = "exec/Surface_iPhone/out"

m = Metashape("/opt/micmac/bin/mm3d","micmac_working_directory",output_dir, "FraserBasic", "QuickMac", reuse_wd=False)  # initialisation d'un SFM
#m = Metashape("metashape_working_directory", "exec/ou", 8)
c = CloudCompare("cloudcompare.CloudCompare", "cloudCompare_working_directory", output_dir)  # initialisation de PointCloudProcessor
#d = DetectionMetashape()  # initialisation d'un DetecteurMire
d = DetectionCCTag('/opt/CCTag/', 'cctag_working_directory', output_dir, reuse_wd=False)

# instantiation d'un objet DensityAnalyser construit à partir des modules défini au-dessus
analyser = DensityAnalyser(m, d, c, output_dir)
# analyse du volume des trous présents sur les photos
volumes_trous = analyser.analyse("exec/Surface_iPhone/bef", # à compléter par le dossier contenant les images avant excavation
                                 "exec/Surface_iPhone/aft/",  # à compléter par le dossier contenant les images après excavation
                                 scale_bars,display_padding=True)

print("###########################################################################\n"
      "############################# Fin d'exécution #############################\n"
      "###########################################################################\n\n")
for i in range(len(volumes_trous)):
    print(f"volume du trou n°{i + 1} : {volumes_trous[i]}")




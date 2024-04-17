from Grounded.Tools.DetecteurMire.DetectionCCTag import DetectionCCTag
from Grounded.Tools.SFM import MicMac
from Grounded.Tools.PointCloudProcessor import CloudCompare
from Grounded.DensityAnalyser import DensityAnalyser
from DataObject import PointCloud, Raster

import cv2

m = MicMac("/opt/micmac/bin/mm3d")
c = CloudCompare()
d = DetectionCCTag("/opt/CCTag/")

analyser = DensityAnalyser(m, d, c)
#analyser.analyse("/home/francoin/Documents/Projet_Densite_Sol/Dossier_photo_test/avant",
#                 "/home/francoin/Documents/Projet_Densite_Sol/Dossier_photo_test/apres")
#c.cloud_to_cloud_difference(PointCloud("/home/francoin/Documents/Projet_Densite_Sol/grounded/cloudCompare_working_directory/C3DC_0_TRANSFORMED_2024-04-15_17h23_28_101.ply"),
#                            PointCloud("/home/francoin/Documents/Projet_Densite_Sol/grounded/cloudCompare_working_directory/C3DC_1_TRANSFORMED_2024-04-15_17h23_29_473.ply"))
analyser.test()

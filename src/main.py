from src.Tools.DetecteurMir.DetectionCCTag import DetectionCCTag

detect = DetectionCCTag()
images = detect.detection_mirs("../../02-Essaies/00_DATA")

print(images)

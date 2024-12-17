########### gestion de l'orientation
#on importe la fonction Image de exif en la renommant car on a déjà un dataObject Image
import numpy as np
from exif import Image as exifImage
#on regarde si l'orientation est une orientation paysage par défaut
exifImage('exec/IN/bef/IMG_3534.jpg').orientation.value==1

# boucle pour corriger tableau_image quand l'orientation est à 180° (pour l'instant on ne gère pas les autres)
for im in tableau_image:
    im_width = exifImage(im.path).pixel_x_dimension
    im_height = exifImage(im.path).pixel_y_dimension
    if exifImage(im.path).orientation.value == 3:
        #on est dans le cas de rotation à 180°
        for mire in im.mires_visibles:
            mire.coordinates = np.subtract((im_width,im_height),mire.coordinates)
    elif exifImage(im.path).orientation.value != 1:
        #on est dans le cas où l'orientation n'est ni la rotation à 180° ni l'orientation normale - cas non traité
        print(f"""cas d'orientation d'image "{exifImage(im.path).orientation.name}" non traité""")



########### lecture et afffichage des mires 3D
x=[mire.coordinates[0] for mire in mires_3d]
y=[mire.coordinates[1] for mire in mires_3d]
z=[mire.coordinates[2] for mire in mires_3d]
noms=[mire.identifier for mire in mires_3d]
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
ax.plot(x,y,'o')
for mire in mires_3d:
    ax.annotate('{}'.format(mire.identifier),(mire.coordinates[0],mire.coordinates[1]))

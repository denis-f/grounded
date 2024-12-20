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
import matplotlib
matplotlib.use('Qt5Agg')
fig, ax = plt.subplots()
ax.plot(x,y,'o')
for mire in mires_3d:
    ax.annotate('{}'.format(mire.identifier),(mire.coordinates[0],mire.coordinates[1]))
ax.plot(np.mean(x),np.mean(y),'ro')
x_min=np.min(x)
x_mean=np.mean(x)
x_max=np.max(x)
y_min=np.min(y)
y_mean=np.mean(y)
y_max=np.max(y)
ax.plot(x_min,y_min,'go')
ax.plot(x_min,y_max,'go')
ax.plot(x_max,y_max,'go')
ax.plot(x_max,y_min,'go')
ax.plot(x[np.argmin(x)],y[np.argmin(x)],'ro', mfc='none')
ax.plot(x[np.argmin(y)],y[np.argmin(y)],'ro', mfc='none')
ax.plot(x[np.argmax(y)],y[np.argmax(y)],'ro', mfc='none')
ax.plot(x[np.argmax(x)],y[np.argmax(x)],'o', mfc='none')
# [ à faire une fois qu'on a fait la rotation 3D pour avoir le Z perpendiculaire au plan moyen des mires]
# => on trouve la ligne qui fitte le mieux les mires => les coeffs vont nous donner la rotation autour de Z
slope, intercept = np.polyfit(x, y, 1)
abline_values = [slope * i + intercept for i in x]
plt.plot(x, abline_values, 'b')


#### FIT d'un plan (et représentation)
# l'idée est de transformer le système de coordonnées de manière à ce que
#  - le plan qui fitte les mires soit un plan perpendicaulaire à l'axe Z
#  - que le nouveau Z soit du même côté que l'ancien Z (produit scalaire positif ?)
#  - que les réglets horizontaux soient le plus près de l'horizontale (minimiser la moyenne des delta y sur les coordonnées des réglets)
#  - que les réglets verticaux soient le plus près de la verticale (minimiser la moyenne des delta x sur les coordonnées des réglets verticaux)
#  - que les réglets horizontaux soient en haut
#  Il faut donc d'abord
#  - déterminer quels sont les réglets horizontaux ? les deux points les plus éloignés du barycentre sont forcément les points bas des mires verticales ?

from mpl_toolkits.mplot3d import Axes3D


plt.figure()
ax=plt.subplot(111,projection='3d')
ax.scatter(x,y,z)

def fit_plane(x,y,z):
    tmp_A = []
    tmp_b = []
    for i in range(len(x)):
        tmp_A.append([x[i], y[i], 1])
        tmp_b.append(z[i])
    b = np.matrix(tmp_b).T
    A = np.matrix(tmp_A)
    fit = (A.T * A).I * A.T * b
    errors = b - A * fit
    residual = np.linalg.norm(errors)
    return float(fit[0]), float(fit[1]), float(fit[2]), errors, residual

a, b, c, errors, residual = fit_plane(x,y,z)

print("solution: %f x + %f y + %f = z" % (a, b, c))
print("errors:")
print(errors)
print("residual: {}".format(residual))
xlim = ax.get_xlim()
ylim = ax.get_ylim()
X,Y = np.meshgrid(np.arange(xlim[0], xlim[1]),
                  np.arange(ylim[0], ylim[1]))
Z = np.zeros(X.shape)
for r in range(X.shape[0]):
    for c in range(X.shape[1]):
        Z[r,c] = a * X[r,c] + b * Y[r,c] + c
ax.plot_wireframe(X,Y,Z, color='k')
ax.set_xlabel('x')
ax.set_ylabel('y')
ax.set_zlabel('z')
plt.show()



####







####### Rotationde points sur un plan
import numpy as np
from scipy.linalg import svd

def rotate_points_to_xy_plane(points, a, b, c):
    # Ensure points is a numpy array
    points = np.array(points)

    # Normal vector of the plane
    normal = np.array([a, b, -1])
    normal = normal / np.linalg.norm(normal)

    # If normal[2] is negative, flip the normal to ensure positive Z
    if normal[2] < 0:
        normal = -normal

    # Calculate rotation axis (cross product of normal and [0, 0, 1])
    rotation_axis = np.cross(normal, [0, 0, 1])
    rotation_axis = rotation_axis / np.linalg.norm(rotation_axis)

    # Calculate rotation angle
    cos_theta = np.dot(normal, [0, 0, 1])
    #sin_theta = np.linalg.norm(rotation_axis)
    sin_theta = np.sqrt(1 - cos_theta ** 2)

    # Construct rotation matrix using Rodriguez rotation formula
    K = np.array([[0, -rotation_axis[2], rotation_axis[1]],
                  [rotation_axis[2], 0, -rotation_axis[0]],
                  [-rotation_axis[1], rotation_axis[0], 0]])
    R = np.eye(3) + sin_theta * K + (1 - cos_theta) * np.dot(K, K)

    # Apply rotation to all points
    rotated_points = np.dot(points, R.T)

    return rotated_points

points=np.array([x,y,z]).T

res=rotate_points_to_xy_plane(np.array([x,y,z]).T,a,b,c)
x_1=res[:,0]
y_1=res[:,1]
z_1=res[:,2]

plt.figure()
ax=plt.subplot(111,projection='3d')
ax.scatter(x_1,y_1,z_1)
ax.set_xlabel('x')
ax.set_ylabel('y')
ax.set_zlabel('z')


fig, ax = plt.subplots()
ax.plot(x_1,y_1,'yo')
for mire in mires_3d:
    ax.annotate('{}'.format(mire.identifier),(mire.coordinates[0],mire.coordinates[1]))
ax.plot(np.mean(x_1),np.mean(y_1),'ro')

slope, intercept = np.polyfit(x_1, y_1, 1)
abline_values = [slope * i + intercept for i in x_1]
plt.plot(x_1, abline_values, 'b')



















####### TEST automatisé de version de CloudCompare
import re
#on crée un appel de cloudCompare en logguant les sorties dans un fichier et en appellant l'option CSF, disponible seulement à partir de la 2.12
subprocess([path_cloud_compare, "-SILENT", "-LOG_FILE logCC.txt", "-CSF"],
                        os.path.join(self.working_directory, "Distance.log"))
#On ouvre ensuite ce texte
text_file = open("logCC.txt", "r")
# a priori si pas d'erreur on est en version >=2.12
v2_11_ou_inferieure=False
for line in text_file:
    #on cherche le pattern "Unknown"
    if re.search("Unknown", line):
        #et si c'est associé au pattern "CSF" c'est qu'on est en version 2.11 ou inférieure
        if re.search("CSF", line):
            v2_11_ou_inferieure=True

#######
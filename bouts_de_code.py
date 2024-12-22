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


#sauvegarde point clouds
import trimesh
PTS_0 = trimesh.load(point_cloud_before_excavation.path)
PTS_1 = trimesh.load(point_cloud_after_excavation.path)
import pickle
# Fait une fois pour sauvegarder
# with open('point_clouds.pkl', 'wb') as f:  # Python 3: open(..., 'wb')
#     pickle.dump([PTS_0, PTS_1], f)
with open('point_clouds.pkl','rb') as f:  # Python 3: open(..., 'rb')
    PTS_0, PTS_1 = pickle.load(f)

#on récupère
pts0 = PTS_0.vertices
pts1 = PTS_1.vertices


PTS_0_rotated=PTS_0
PTS_0_rotated.vertices=rotate_points_to_xy_plane(PTS_0.vertices,a,b,c)
out_file=open('pts0rotated.ply','wb')
out_file.write(trimesh.exchange.ply.export_ply(PTS_0_rotated))
out_file.close()

PTS_1_rotated=PTS_1
PTS_1_rotated.vertices=rotate_points_to_xy_plane(PTS_1.vertices,a,b,c)
out_file=open('pts1rotated.ply','wb')
out_file.write(trimesh.exchange.ply.export_ply(PTS_1_rotated))
out_file.close()



########### lecture et afffichage des mires 3D
import pickle
import numpy as np
with open('xyz.pkl','rb') as f:  # Python 3: open(..., 'rb')
    x, y, z, mires_3d = pickle.load(f)

x=[mire.coordinates[0] for mire in mires_3d]
y=[mire.coordinates[1] for mire in mires_3d]
z=[mire.coordinates[2] for mire in mires_3d]
noms=[mire.identifier for mire in mires_3d]
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("TkAgg")
fig, ax = plt.subplots()
ax.plot(x,y,'o')
for mire in mires_3d:
    ax.annotate('{}'.format(mire.identifier),(mire.coordinates[0],mire.coordinates[1]))
ax.plot(np.mean(x),np.mean(y),'ro')
# x_min=np.min(x)
# x_mean=np.mean(x)
# x_max=np.max(x)
# y_min=np.min(y)
# y_mean=np.mean(y)
# y_max=np.max(y)
# ax.plot(x_min,y_min,'go')
# ax.plot(x_min,y_max,'go')
# ax.plot(x_max,y_max,'go')
# ax.plot(x_max,y_min,'go')
# ax.plot(x[np.argmin(x)],y[np.argmin(x)],'ro', mfc='none')
# ax.plot(x[np.argmin(y)],y[np.argmin(y)],'ro', mfc='none')
# ax.plot(x[np.argmax(y)],y[np.argmax(y)],'ro', mfc='none')
# ax.plot(x[np.argmax(x)],y[np.argmax(x)],'o', mfc='none')


#### FIT d'un plan (et représentation)
# l'idée est de transformer le système de coordonnées de manière à ce que
#  - le plan qui fitte les mires soit un plan perpendiaulaire à l'axe Z
#  - que le nouveau Z soit du même côté que l'ancien Z (produit scalaire positif ?)
#  - que les réglets horizontaux soient le plus près de l'horizontale (minimiser la moyenne des delta y sur les coordonnées des réglets)
#  - que les réglets verticaux soient le plus près de la verticale (minimiser la moyenne des delta x sur les coordonnées des réglets verticaux)
#  - que les réglets horizontaux soient en haut
#  Il faut donc d'abord
#  - déterminer quels sont les réglets horizontaux ? les deux points les plus éloignés du barycentre sont forcément les points bas des mires verticales ?

from mpl_toolkits.mplot3d import Axes3D


# Issu de https://stackoverflow.com/a/44315488
plt.figure()
ax=plt.subplot(111,projection='3d')
ax.scatter(x,y,z)
ax.set_aspect('equal')

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
    return fit[0,0], fit[1,0], fit[2,0], errors, residual

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
    for s in range(X.shape[1]):
        Z[r,s] = a * X[r,s] + b * Y[r,s] + c
ax.plot_wireframe(X,Y,Z, color='k')
ax.set_xlabel('x')
ax.set_ylabel('y')
ax.set_zlabel('z')
plt.show()



####







####### Rotation de points sur un plan - issu de perplexity
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

#points=np.array([x,y,z]).T

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

# mise à jour des coordonnées des mires
for i in np.arange(len(mires_3d)):
    mires_3d[i].coordinates = (x_1[i], y_1[i], z_1[i])

fig, ax = plt.subplots()
ax.plot(x_1,y_1,'yo')

# les lignes suivantes ne marchent plus car les coordonnées ont changé
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
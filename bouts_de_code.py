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
with open('exec/xyz.pkl','rb') as f:  # Python 3: open(..., 'rb')
    x, y, z, mires_3d = pickle.load(f)

x=[mire.coordinates[0] for mire in mires_3d]
y=[mire.coordinates[1] for mire in mires_3d]
z=[mire.coordinates[2] for mire in mires_3d]
noms=[mire.identifier for mire in mires_3d]
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("TkAgg")
fig, ax = plt.subplots()
ax.set_aspect('equal', adjustable='box')
ax.plot(x,y,'o')
for mire in mires_3d:
    ax.annotate('{}'.format(mire.identifier),(mire.coordinates[0],mire.coordinates[1]))
ax.plot(np.median(x),np.median(y),'ro')

# def box_centre(x,y):
#     return (np.min(x)+np.max(x))/2,(np.min(y)+np.max(y))/2

box_centre_x, box_centre_y = (np.min(x) + np.max(x)) / 2, (np.min(y) + np.max(y)) / 2
#ax.plot(box_centre(x,y)[0],box_centre(x,y)[1],'go')
ax.plot(box_centre_x,box_centre_y,'go')

# l'angle de la rotation pour passer d'un vecteur (x,y) à un vecteur (0,1) c'est arctan (x/y) on fait donc arctan2(x,y)
# voir arctan2 https://numpy.org/doc/2.1/reference/generated/numpy.arctan2.html#numpy.arctan2
angle = np.arctan2((np.median(x) - box_centre_x), (np.median(y) - box_centre_y))



#plt.plot([np.median(x),box_centre(x,y)[0]],[np.median(y),box_centre(x,y)[1]])
#plt.arrow(box_centre(x,y)[0],box_centre(x,y)[1],np.median(x)-box_centre(x,y)[0],np.median(y)-box_centre(x,y)[1],width=0.03,length_includes_head=True)
plt.arrow(box_centre_x,box_centre_y,np.median(x)-box_centre_x,np.median(y)-box_centre_y,width=0.03,length_includes_head=True)

# def rot(xy, angle):
#     #/!\ xy doit avoir la forme [x,y] /!\
#     # ce serait bien de faire une vérification ici / tentative (pas sûr que ça marche
#     if type(xy)==list:
#         if len(xy)==2:
            rotmat = np.array([[np.cos(angle), -np.sin(angle)],
                               [np.sin(angle), np.cos(angle)]])
    #         return np.dot(rotmat, xy)
    #     else : print(f"probleme : {xy} n'est pas une liste à deux éléments, rotation d'angle {angle} impossible")
    # else:
    #     print(f"probleme : {xy} n'est pas une liste, rotation d'angle {angle} impossible")

x1,y1 = np.dot(rotmat, [x, y])
box_centre_x1, box_centre_y1 = (np.min(x1) + np.max(x1)) / 2, (np.min(y1) + np.max(y1)) / 2
# [x1,y1] = rot([x, y], np.arctan2 ( (np.median(x)-box_centre(x,y)[0]), (np.median(y)-box_centre(x,y)[1]) ) )

# [x1,y1] = rot([x, y],- 3.14/12 )

ax.plot(x1,y1,'.')
ax.plot(np.median(x1),np.median(y1),'r.')
#ax.plot(box_centre(x1,y1)[0],box_centre(x1,y1)[1],'g.')
ax.plot(box_centre_x1,box_centre_y1,'g.')
plt.arrow(box_centre_x1,box_centre_y1,np.median(x1)-box_centre_x1,np.median(y1)-box_centre_y1,width=0.03,length_includes_head=True)


x_min=np.min(x)
x_max=np.max(x)
y_min=np.min(y)
y_max=np.max(y)

# ax.plot(x_min,y_min,'go')
# ax.plot(x_min,y_max,'go')
# ax.plot(x_max,y_max,'go')
# ax.plot(x_max,y_min,'go')
# ax.plot(x[np.argmin(x)],y[np.argmin(x)],'ro', mfc='none')
# ax.plot(x[np.argmin(y)],y[np.argmin(y)],'ro', mfc='none')
# ax.plot(x[np.argmax(y)],y[np.argmax(y)],'ro', mfc='none')
# ax.plot(x[np.argmax(x)],y[np.argmax(x)],'o', mfc='none')

### rotation des mires dans le plan xy pour que les mires horizontales soient en haut et les mires verticales soient verticales
# on postule que le "bas" est défini par l'endroit où il n'y a pas de réglet
#   => c'est raccord avec la config en vertical/fosse =  le bas est le côté où est le bac de prélévèement
#   => c'est raccord avec la config en horizontal/par-dessus = le "bas" est le côté où se situe l'opérateur qui prélève, on laisse un côté sans mire pour simplifier
# dans ce cas de figure le barycentre des mires sera tiré du côté opposé où il n'y a pas de mire.
# on calcule le barycentre des mires avec la médiane (moins sensible aux extrèmes) => point H
# on calcule le point milieu du rectangle englobant => point O
# => la verticale orientée vers le haut est définie par le vecteur OH

bary_mires=np.median(x),np.median(y)
dists=[]
for index,scale_bar in enumerate(scale_bars):
    first_mire,last_mire=scale_bar.start.identifier,scale_bar.end.identifier
    first_mire_coords = mires_3d[[mire.identifier for mire in mires_3d].index(first_mire)].coordinates[0:2]
    last_mire_coords = mires_3d[[mire.identifier for mire in mires_3d].index(last_mire)].coordinates[0:2]
    scale_bar_middle_coords = np.add(first_mire_coords,last_mire_coords)/2
    dists.append(np.linalg.norm( scale_bar_middle_coords - bary_mires))
scale_bars_up=np.array(scale_bars)[np.argsort(dists)[:(len(scale_bars)-2)]].tolist()

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

def affichage_3d(x,y,z,a,b,c,errors,residual):
    plt.figure()
    ax=plt.subplot(111,projection='3d')
    ax.scatter(x,y,z)
    ax.set_aspect('equal')
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

res=rotate_points_to_xy_plane(np.array([x,y,z]).T,a,b,c)
def affichage_mires_2(res,mires_3d):
    x_1=res[:,0]
    y_1=res[:,1]
    z_1=res[:,2]
    #plot3d
    plt.figure()
    ax=plt.subplot(111,projection='3d')
    ax.scatter(x_1,y_1,z_1)
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.set_zlabel('z')

    # mise à jour des coordonnées des mires
    for i in np.arange(len(mires_3d)):
        mires_3d[i].coordinates = (x_1[i], y_1[i], z_1[i])

    #plot2d
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
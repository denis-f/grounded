import trimesh
import numpy as np
from scipy.spatial import ConvexHull
from scipy.spatial import Delaunay
from skimage import measure
import rasterio
from rasterio.transform import from_origin
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
import scipy.ndimage
from shapely.geometry import Polygon
from shapely.geometry.polygon import LinearRing
from shapely.ops import unary_union
from shapely.geometry import Polygon, Point
import cv2
import open3d as o3d
from scipy.spatial import cKDTree

# | Load point clouds            Fabrice Vinatier  | ----------------------------------------------

PTS_0 = trimesh.load('IN/2018-10_Mauguio/Photogrammetrie/DenseClouds/Fosse3_H2_V_BEFORE.ply')
PTS_1 = trimesh.load('IN/2018-10_Mauguio/Photogrammetrie/DenseClouds/Fosse3_H2_V_AFTER.ply')
pts0 = PTS_0.vertices
pts1 = PTS_1.vertices


# | Rasterization of point clouds            Fabrice Vinatier  | ----------------------------------------------

def project_cloud(pts):
    x_coords = pts[:, 0]
    y_coords = pts[:, 1]
    values = pts[:, 2]
    min_x, min_y = np.min(x_coords), np.min(y_coords)
    max_x, max_y = np.max(x_coords), np.max(y_coords)
    resolution = 0.001  # Planimetric resolution
    width = int((max_x - min_x) / resolution) + 1
    height = int((max_y - min_y) / resolution) + 1
    raster_data = np.full((height, width), np.nan)
    for x, y, value in pts:
        row = int((max_y - y) / resolution)
        col = int((x - min_x) / resolution)
        raster_data[row, col] = value
    transform = [min_x, max_y, resolution]
    return raster_data, transform


r0, t0 = project_cloud(pts0)
r1, t1 = project_cloud(pts1)
rD = r0 - r1

# ------------- Visualisation--------------------------#
scale_x = t0[2]
scale_y = t0[2]
origin_x = t0[0]
origin_y = t0[1]
cols = rD.shape[1]
rows = rD.shape[0]

plt.imshow(rD, extent=[origin_x, origin_x + cols * scale_x, origin_y + rows * scale_y, origin_y], cmap='gray',
           origin='upper')
plt.title('Projected Points on Raster')
plt.xlabel('X Coordinate')
plt.ylabel('Y Coordinate')
plt.show()
# ----------------------------------------------------#

# | Delimitate border of excavated holes            Fabrice Vinatier  | ----------------------------------------------

thres_z = 0.002
thres_area = 0.01
thres_buffer = 0.02


def inverse_transform(indices, transform):
    min_x, max_y, resolution = transform
    i = indices[:, 0]
    j = indices[:, 1]
    x = min_x + j * resolution
    y = max_y - i * resolution
    return np.vstack((x, y)).T


def calculate_polygon_area(contour):
    x = contour[:, 1]
    y = contour[:, 0]
    return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))


def find_holes(raster=rD, thres_z=0.005, thres_area=0.01, thres_buffer=0.02):
    contours = measure.find_contours(rD, -thres_z)
    holes = []
    for contour in contours:
        hole = inverse_transform(contour, t1)
        holes.append(hole)
    filtered_holes = [hole for hole in holes if calculate_polygon_area(hole) > thres_area]
    buffered_holes = []
    for hole in filtered_holes:
        poly = Polygon(hole)
        if poly.is_valid and not poly.is_empty:
            buffered_poly = poly.buffer(thres_buffer)
            buffered_holes.append(buffered_poly)
    return (buffered_holes)


holes = find_holes(rD)

# ------------- Visualisation--------------------------#
plt.imshow(rD, extent=[origin_x, origin_x + cols * scale_x, origin_y + rows * scale_y, origin_y], cmap='viridis',
           origin='upper')
for hole in holes:
    x, y = hole.exterior.xy  # Extraction des coordonnées x et y
    plt.plot(x, 2 * origin_y - y, color='r')  # Tracé du polygone en rouge
plt.show()
plt.close()


# ----------------------------------------------------#

# | Crop cloud according to contours         Fabrice Vinatier  | ----------------------------------------------

def cut_cloud_by_polygon(pts, poly):
    points_in_polygon = [point for point in pts if Point(point[0], point[1]).within(poly)]
    return np.vstack(points_in_polygon)


def cut_cloud_by_polygon_optimized_3d(pts, poly):
    pts_array = np.asarray(pts)
    mask = np.zeros(len(pts_array), dtype=bool)
    xy_points = pts_array[:, :2]
    for i, (x, y) in enumerate(xy_points):
        mask[i] = poly.contains(Point(x, y))
    return pts_array[mask]


def crop_pts(pts, poly):
    pts_f = pts[
        (pts[:, 0] >= poly.bounds[0]) & (pts[:, 0] <= poly.bounds[2]) &
        (pts[:, 1] >= poly.bounds[1]) & (pts[:, 1] <= poly.bounds[3])
        ]
    return (pts_f)


def create_mesh(pts):
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(pts)
    pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.001, max_nn=5))
    msh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd, depth=7)
    msh.compute_vertex_normals()
    msh.paint_uniform_color([0.1, 0.1, 0.1])
    return (msh)


poly = holes[0]
pts0_c = crop_pts(pts0, poly)
pts0_cc = cut_cloud_by_polygon_optimized_3d(pts0_c, poly)
pts1_c = crop_pts(pts1, poly)
pts1_cc = cut_cloud_by_polygon(pts1_c, poly)
pts_tot = np.vstack((pts1_cc, pts0_cc))

pcd = o3d.geometry.PointCloud()
pcd.points = o3d.utility.Vector3dVector(pts_tot)
#
# R = pcd.get_rotation_matrix_from_xyz((0, 0, np.pi/2))
# pcd = pcd.rotate(R, center=(0, 0, 0))
#
# o3d.visualization.draw_geometries([pcd],mesh_show_back_face=True)

msh_tot = create_mesh(pts_tot)

# R = msh_tot.get_rotation_matrix_from_xyz((np.pi/2, 0, 0))

# Appliquez la rotation
# msh_tot.rotate(R, center=(0, 0, 0))
#
# msh_tot.remove_degenerate_triangles()
# msh_tot.remove_duplicated_triangles()
# msh_tot.remove_unreferenced_vertices()

# msh_tot.is_watertight()
#
#
# # Extraire les sommets (vertices) et les triangles (faces) du mesh Open3D
# vertices = np.asarray(msh_tot.vertices)
# triangles = np.asarray(msh_tot.triangles)
#
# # Créer un maillage Trimesh à partir des sommets et des triangles
# mesh_trimesh = trimesh.Trimesh(vertices=vertices, faces=triangles)
# mesh_trimesh.fill_holes()
#
# mesh_trimesh.export('msh_tot_mesh.obj')


# ------------- Visualisation--------------------------#
o3d.visualization.draw_geometries([msh_tot], mesh_show_back_face=True)


# ----------------------------------------------------#

# | Crop mesh cloud according to contours         Fabrice Vinatier  | ----------------------------------------------


def nearest_neighbor_distance(pts1, pts2):
    tree = cKDTree(pts2)
    distances, _ = tree.query(pts1)
    return distances


# nearest_neighbor_distance(pts1,pts0)


def cut_mesh_by_polygon(mesh_o3d, poly):
    vertices = np.asarray(mesh_o3d.vertices)
    faces = np.asarray(mesh_o3d.triangles)
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
    inside_faces = [face for face in mesh.faces
                    if all(poly.contains(Point(*mesh.vertices[v][:2])) for v in face)]
    sub_mesh = o3d.geometry.TriangleMesh()
    sub_mesh.vertices = o3d.utility.Vector3dVector(mesh.vertices)
    sub_mesh.triangles = o3d.utility.Vector3iVector(inside_faces)
    sub_mesh.compute_vertex_normals()
    sub_mesh.paint_uniform_color([0.7, 0.7, 0.7])
    return sub_mesh


def get_crown_vertices(mesh):
    mesh.compute_vertex_normals()
    mesh.compute_triangle_normals()
    triangles = np.asarray(mesh.triangles)
    vertices = np.asarray(mesh.vertices)
    edge_count = {}
    for triangle in triangles:
        for i in range(3):
            edge = tuple(sorted((triangle[i], triangle[(i + 1) % 3])))
            edge_count[edge] = edge_count.get(edge, 0) + 1
    boundary_edges = [edge for edge, count in edge_count.items() if count == 1]
    boundary_vertices = set()
    for edge in boundary_edges:
        boundary_vertices.update(edge)
    vertices = np.asarray(mesh.vertices)
    boundary_coordinates = vertices[list(boundary_vertices)]
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(boundary_coordinates)
    return (pcd)


poly = holes[1]
pts0_c = crop_pts(pts0, poly)
pts0_cc = cut_cloud_by_polygon(pts0_c, poly)
msh0 = create_mesh(pts0_c)
msh0_c = cut_mesh_by_polygon(msh0, poly)
pts1_c = crop_pts(pts1, poly)
pts1_cc = cut_cloud_by_polygon(pts1_c, poly)
msh1 = create_mesh(pts1_c)
msh1_c = cut_mesh_by_polygon(msh1, poly)
cr0 = get_crown_vertices(msh0_c)
cr1 = get_crown_vertices(msh1_c)
pts_tot = np.vstack((pts1_cc, pts0_cc))

pcd = o3d.geometry.PointCloud()
pcd.points = o3d.utility.Vector3dVector(pts_tot)

# ------------- Visualisation--------------------------#
o3d.visualization.draw_geometries([msh0, msh1, msh0_c, msh1_c, cr0, cr1], mesh_show_back_face=True)
o3d.visualization.draw_geometries([msh0_c, msh1_c, cr0, cr1, pcd], mesh_show_back_face=True)

# ----------------------------------------------------#

# | Extrude each crown         Fabrice Vinatier  | ----------------------------------------------


# | Extrude each crown         Fabrice Vinatier  | ----------------------------------------------

# Supposons que msh0_c soit déjà un mesh de trimesh
# Récupérer les points et faces de msh0_c
points_c = np.asarray(msh0_c.vertices)  # Sommets de msh0_c
faces_c = np.asarray(msh0_c.triangles)  # Faces de msh0_c

z_delta = 0.5

circle_points = np.asarray(cr0.points)
num_points = len(circle_points)

# On projette les points sur le plan XY (en ignorant la coordonnée z)
circle_points_2d = circle_points[:, :2]

# Calcul du barycentre des points projetés (centre du nuage dans le plan XY)
center_2d = np.mean(circle_points_2d, axis=0)


# Fonction pour calculer l'angle par rapport au centre dans le plan XY
def angle_from_center_2d(point):
    return np.arctan2(point[1] - center_2d[1], point[0] - center_2d[0])


# Calcul des angles pour les points projetés
angles = np.apply_along_axis(angle_from_center_2d, 1, circle_points_2d)

# Tri des points originaux 3D selon l'angle dans le plan XY (sens horaire)
circle_points = circle_points[np.argsort(-angles)]

# Création des deux nuages de points
circle_points_z0 = circle_points  # Premier nuage avec Z = 0
circle_points_z1 = circle_points.copy()
circle_points_z1[:, 2] = z_delta  # Deuxième nuage avec Z décalé

# Fusionner les points des deux cercles en un seul ensemble de points
points = np.vstack((circle_points_z0, circle_points_z1))

# Création des faces (triangles ou quadrangles) entre les points des deux nuages
triangles = []
for i in range(num_points):
    next_i = (i + 1) % num_points  # Boucler au début après le dernier point

    # Créer des triangles pour relier les points des deux cercles
    triangles.append([i, next_i, num_points + i])  # Triangle reliant (z=0)
    triangles.append([next_i, num_points + next_i, num_points + i])  # Triangle reliant (z=0.01)

# Point central pour la triangulation (avec Z = z_delta)
center_point = np.array([center_2d[0], center_2d[1], z_delta])

# Ajouter le point central au tableau des points
points = np.vstack((points, center_point))

# Index du point central (le dernier point ajouté)
center_index = len(points) - 1

# Créer des triangles en reliant le point central aux points du cercle à Z = z_delta
for i in range(num_points):
    next_i = (i + 1) % num_points  # Boucler au début après le dernier point
    triangles.append([center_index, num_points + i, num_points + next_i])

# Ajouter les points de msh0_c à l'ensemble des points existants
points = np.vstack((points, points_c))

# Ajuster les indices des faces de msh0_c pour qu'ils correspondent aux nouveaux indices des points
# Le décalage est le nombre total de points déjà présents dans "points"
face_index_offset = len(points) - len(points_c)  # Décalage pour les indices

# Ajuster les indices des faces de msh0_c
faces_c_adjusted = faces_c + face_index_offset

# Ajouter les faces ajustées à la liste des triangles existants
triangles.extend(faces_c_adjusted)

# Création du mesh
mesh = o3d.geometry.TriangleMesh()
mesh.vertices = o3d.utility.Vector3dVector(points)
mesh.triangles = o3d.utility.Vector3iVector(triangles)

# Optionnel : calcul des normales pour un meilleur affichage
mesh.compute_vertex_normals()

# Visualisation du mesh
o3d.visualization.draw_geometries([mesh])

# Fusionner les sommets proches (distance_threshold est la tolérance)
mesh.remove_duplicated_vertices()
mesh.remove_degenerate_triangles()
mesh.remove_unreferenced_vertices()

vertices = np.asarray(mesh.vertices)
triangles = np.asarray(mesh.triangles)

# Créer un mesh Trimesh à partir des données Open3D
mesh_trimesh = trimesh.Trimesh(vertices=vertices, faces=triangles)

# Remplir automatiquement les trous du mesh
mesh_trimesh.fill_holes()
tolerance = 1e-6
mesh_trimesh.merge_vertices()

# Vérifier à nouveau l'étanchéité après le remplissage des trous
mesh_trimesh.is_watertight

# Reconvertir le mesh Trimesh vers Open3D
mesh_o3d_new = o3d.geometry.TriangleMesh()

# Remplir les vertices et triangles avec les données de Trimesh
mesh_o3d_new.vertices = o3d.utility.Vector3dVector(mesh_trimesh.vertices)
mesh_o3d_new.triangles = o3d.utility.Vector3iVector(mesh_trimesh.faces)
mesh_o3d_new.compute_vertex_normals()

# Afficher le mesh avec Open3D
o3d.visualization.draw_geometries([mesh_o3d_new])

# Visualisation du mesh
o3d.visualization.draw_geometries([mesh_trimesh])

mesh_trimesh.export('watertight_mesh.obj')
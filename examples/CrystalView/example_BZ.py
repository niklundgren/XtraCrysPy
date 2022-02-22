from XtraCrysPy import XtraCrysPy as XCP
import numpy as np

# Lattice Vectors
alat = 4
a_vec = alat * np.array([[1,0,0],[1/2,np.sqrt(3)/2,0],[0,0,1]])

# Volume
omega = a_vec[0] @ np.cross(a_vec[1], a_vec[2])

# Reciprocal Lattice Vectors
b_vec = np.zeros_like(a_vec)
b_vec[0,:] = 2*np.pi/omega * np.cross(a_vec[1], a_vec[2])
b_vec[1,:] = 2*np.pi/omega * np.cross(a_vec[2], a_vec[0])
b_vec[2,:] = 2*np.pi/omega * np.cross(a_vec[0], a_vec[1])

# Start XtraCrysPy
xcp = XCP.XtraCrysPy()
xcp.start_cryspy_view()
xcp.view.draw_BZ_boundary(b_vec=b_vec)

# Gamma
green = [0,1,0]
gamma = [[0,0,0]]
xcp.view.draw_BZ_points(gamma, green, b_vec)

# H points
red = [1,0,0]
points_H = []
for xy in [[2/3,1/3],[1/3,2/3],[-2/3,-1/3],[-1/3,-2/3],[1/3,-1/3],[-1/3,1/3]]:
  # Top
  v = np.array([xy[0], xy[1], 1/2])
  points_H.append(v @ b_vec)
  # Bottom
  v = np.array([xy[0], xy[1], -1/2])
  points_H.append(v @ b_vec)
xcp.view.draw_BZ_points(points_H, red, b_vec)

# M points
blue = [0,0,1]
points_M = []
for xy in [[.5,0],[0,.5],[-.5,0],[0,-.5],[.5,.5],[-.5,-.5]]:
  v = np.array([xy[0], xy[1], 0])
  points_M.append(v @ b_vec)
xcp.view.draw_BZ_points(points_M, blue, b_vec)

"""

    lettucethink-python - Python tools for the LettuceThink robot

    Copyright (C) 2018 Sony Computer Science Laboratories
    Authors: D. Colliaux, T. Wintz, P. Hanappe
  
    This file is part of lettucethink-python.

    lettucethink-python is free software: you can redistribute it
    and/or modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation, either
    version 3 of the License, or (at your option) any later version.

    lettucethink-python is distributed in the hope that it will be
    useful, but WITHOUT ANY WARRANTY; without even the implied
    warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with lettucethink-python.  If not, see
    <https://www.gnu.org/licenses/>.

"""    
import math
import cv2
import numpy as np
from lettucethink import svg, log
import lettucethink.cv as lcv

def circle(center_x, center_y, z, tilt, radius, num_points):
   res = []
   for i in range(num_points):
       angle = 2*i*math.pi / num_points
       x = center_x - radius * math.cos(angle)
       y = center_y - radius * math.sin(angle)
       res.append((x, y, z, angle, tilt))
   return res

def line(origin, y, z, length, num_points):
   res = []
   for i in range(num_points):
       x = origin+i* length/ num_points
       res.append((x, 0, 0))
   return res

# Make a boustrophedon. The path goes up and down along the y-axis,
# and slowly moves forward in the x-direction.
# 
# xstart, ystart: the coordinates of the starting point 
#
# dx: the amount to move forward in the x-direction. The path starts
# at xstart, and advance by dx after every sweep along the y-axis.
#
# dy: the amount to move in the y-direction. The path with go back and
# forth between ystart and ystart+dy.
#
# xmax: the maximum value of x, at which the path should stop.
def make_boustrophedon(xstart, ystart, dx, dy, xmax):
   xoff = xstart
   x = [xstart]
   y = [ystart]
   while xoff < xmax:
      x0 = xoff
      x1 = xoff + dx
      x2 = xoff + 2 * dx
      y0 = ystart
      y1 = ystart + dy
      x.append(x0), y.append(y1)
      if x1 < xmax:
         x.append(x1), y.append(y1)
         x.append(x1), y.append(y0)
      if x2 < xmax:
         x.append(x2), y.append(y0)
      xoff += 2 * dx
   return np.array([x,y])


def compute_modified_boustrophedon(mask, toolsize, workspace,
                                   eps_contours=5, eps_toolpath=5,
                                   numFillPoints=5000):

   # Compute boustrophedon ignoring the plants. All coordinates are in
   # image pixels. The boustrophedon start at y=0 (top of image),
   # because that is where the CNC arm is when the image is taken.
   boustro = make_boustrophedon(0, 0, toolsize, workspace.height - 1, workspace.width)

   # Detect i/o points of paths passing through plants
   dense_boustro = fill_with_points(boustro, numFillPoints)
   path_values = mask[(dense_boustro[1]).astype(int), (dense_boustro[0]).astype(int)]
   
   contours = lcv.get_plant_contours(mask.copy())

   #MultiMask is like mask but with multiple labels 
   mm = np.zeros_like(mask)
   multi_mask = np.zeros_like(mask).astype(np.float64)
   for i in range(len(contours)): 
      multi_mask += cv2.fillPoly(mm, contours[:i], [255,255,255]).astype(np.float64)/255

   path_values_multi = multi_mask[(dense_boustro[1]).astype(int),(dense_boustro[0]).astype(int)]

   black_points = np.where(path_values==0)[0]
   if len(black_points) == 0:
      return np.array([[], []])
      
   if path_values[0]: 
      fpath = np.where(path_values==0)[0]
      if len(fpath) > 0:
         dense_boustro = dense_boustro[:,fpath[0]:]
         path_values = path_values[fpath[0]:]
         path_values_multi = path_values_multi[fpath[0]:]
   if path_values[-1]: 
      fpath = np.where(path_values==0)[0]  
      if len(fpath) > 0:
         dense_boustro = dense_boustro[:,:fpath[-1]]
         path_values = path_values[:fpath[-1]]
         path_values_multi = path_values_multi[:fpath[-1]]

   indexes = np.where(np.diff(path_values) > 0)[0]
   io_points = dense_boustro[:, indexes]
   #id_points=dense_boustro[:,idxs+1]
   io_points_ids=path_values_multi[indexes+1]

   # Downsample and compute center of plant contours    
   s_tr = []
   trc = []

   for contour in contours:
      s_tr.append(rdp(contour, eps_contours))
      if len(trc):
         trc = np.vstack([trc, s_tr[-1].mean(axis=0)])
      else:
         trc = s_tr[-1].mean(axis=0)

   # Generate the mofified boustrophedon
   toolpath = np.array([dense_boustro[:,0]]).T
   toolpath = np.hstack([toolpath, dense_boustro[:,:indexes[0]]])
   
   for k in range(int(len(io_points[0])//2)):
      pi = io_points[:,2*k]   #in point
      po = io_points[:,2*k+1] #out point
      #plant = ((.5*(pi+po)-trc)**2).sum(axis=1).argmin() #plant attached to i/o points
      plant = len(contours) - int(io_points_ids[2*k]) - 1
      cor_path = corrected_path(pi, po, s_tr[plant])      
      toolpath = np.hstack([toolpath,cor_path])
      if k < (len(io_points[0])/2-1):
         toolpath = np.hstack([toolpath, dense_boustro[:,indexes[2*k+1]:indexes[2*k+2]]])

   toolpath = np.hstack([toolpath, dense_boustro[:,indexes[2*k+1]:]])
   toolpath = rdp(toolpath.T, eps_toolpath)

   if log.is_enabled():
      render_path(mask, toolpath.T, log.make_image_path("toolpath"))

   return toolpath.T


def render_path(mask, path, filepath):
   stp = np.round(path.T, 0).reshape((-1,1,2)).astype(np.int32)
   cv2.polylines(mask, [stp], False, [145,235,229],8)
   cv2.imwrite(filepath, mask)


def save_to_svg(path, bgimage, width, height, filepath):
   doc = svg.SVGDocument(filepath, width, height)
   doc.add_image(bgimage, 0, 0, width, height)
   if len(path[0]) > 1:
      doc.add_path(path[0], path[1])
   doc.close()

   
def fill_with_points(xy, numberOfPoints):
   ts = np.linspace(0, len(xy[0]), num=len(xy[0]), endpoint=True)
   nts = np.linspace(0, len(xy[0]), num=numberOfPoints, endpoint=True)
   fx = np.interp(nts, ts, xy[0])
   fy = np.interp(nts, ts, xy[1])
   return np.array([fx, fy])


def point_line_distance(point, start, end):
    if (start == end).all():
        return np.linalg.norm(point-start)
    else:
        n = np.linalg.norm(np.linalg.det([end - start, start - point]))
        d = np.linalg.norm(end-start)
        return n/d

     
def rdp(points, epsilon):
    """
    Cartographic generalization is achieved with the Ramer-Douglas-Peucker algorithm
    pseudo-code: http://en.wikipedia.org/wiki/Ramer-Douglas-Peucker_algorithm
    python port: http://github.com/sebleier/RDP
    """
    dmax = 0.0
    index = -1
    for i in range(1, len(points) - 1):
        d = point_line_distance(points[i], points[0], points[-1])
        if d > dmax:
            index = i
            dmax = d
    if dmax >= epsilon:
        res1 = rdp(points[:index+1], epsilon)
        res2 = rdp(points[index:], epsilon)
        return np.vstack([res1[:-1],res2])
    else:
        return np.vstack([points[0], points[-1]])

 
def corrected_path(pi, po, tr, Nfp=200):
   """
   Substitute path passing through plants by shortest contour connecting i/o points 
   """
   longtr = fill_with_points(tr.T, Nfp) 
   pi_idx = ((pi[:,np.newaxis]-longtr)**2).sum(axis=0).argmin()
   po_idx = ((po[:,np.newaxis]-longtr)**2).sum(axis=0).argmin()

   if (pi_idx < po_idx):
      p1 = longtr[:,pi_idx:po_idx]
      p2 = longtr.take(range(-(Nfp-po_idx), pi_idx), axis=1, mode="wrap")[:,::-1]
   else:
      p1 = longtr[:,::-1][:,Nfp-pi_idx:Nfp-po_idx]
      p2 = longtr.take(range(-(Nfp-pi_idx), po_idx), axis=1, mode="wrap")

   d1 = (np.diff(p1,axis=1)**2).sum()
   d2 = (np.diff(p2,axis=1)**2).sum()
   if (d1 <= d2):
      return p1
   else:
      return p2


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
import numpy as np
from lettucethink import svg, log

def circle(xc, yc, z, tilt, radius, num_points):
   res = []
   for i in range(num_points):
       angle = 2*i*math.pi / num_points
       x = xc - radius * math.cos(angle)
       y = yc - radius * math.sin(angle)
       res.append((x, y, z, angle, tilt))
   return res

def line(origin, end, n_points):
    assert(len(origin) == len(end))
    assert(len(origin) == 5)
    origin = np.array(origin)
    end = np.array(end)
    res = []

    for i in range(n_points):
        res.append((1 - i/(n_points-1))*origin + (i /(n_points-1)) * end)
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

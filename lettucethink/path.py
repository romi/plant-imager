import math
import cv2
import numpy as np
from lettucethink import svg
import lettucethink.cv as lcv


def circle(center_x, center_y, z, tilt, radius, num_points):
   res = []
   for i in range(num_points):
       angle = 2*i*math.pi / num_points
       x = center_x - radius * math.cos(angle)
       y = center_y - radius * math.sin(angle)
       res.append((x, y, z, angle, tilt))
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
def makeBoustrophedon(xstart, ystart, dx, dy, xmax):
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


def computeModifiedBoustrophedon(mask, toolsize, workspace, logger,
                                 eps_contours=5, eps_toolpath=5,
                                 numFillPoints=5000):

   # Compute boustrophedon ignoring the plants. All coordinates are in
   # image pixels. The boustrophedon start at y=0 (top of image),
   # because that is where the CNC arm is when the image is taken.
   boustro = makeBoustrophedon(0, 0, toolsize, workspace.height - 1, workspace.width)

   # Detect i/o points of paths passing through plants
   dense_boustro = fillWithPoints(boustro, numFillPoints)
   pathValues = mask[(dense_boustro[1]).astype(int), (dense_boustro[0]).astype(int)]

   blackPoints = np.where(pathValues==0)[0]
   if len(blackPoints) == 0:
      return np.array([[], []])
      
   if pathValues[0]: 
      fpath = np.where(pathValues==0)[0]
      if len(fpath) > 0:
         dense_boustro = dense_boustro[:,fpath[0]:]
         pathValues = pathValues[fpath[0]:]
      
   if pathValues[-1]: 
      fpath = np.where(pathValues==0)[0]  
      if len(fpath) > 0:
         dense_boustro = dense_boustro[:,:fpath[-1]]
         pathValues = pathValues[:fpath[-1]]

   indexes = np.where(np.diff(pathValues) > 0)[0]
   io_points = dense_boustro[:, indexes]

   # Extract plant contours 
   contours = lcv.plantContours(mask.copy())

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
   toolPath = np.array([dense_boustro[:,0]]).T
   toolPath = np.hstack([toolPath, dense_boustro[:,:indexes[0]]])
   
   for k in range(int(len(io_points[0])//2)):
      pi = io_points[:,2*k]   #in point
      po = io_points[:,2*k+1] #out point
      plant = ((.5*(pi+po)-trc)**2).sum(axis=1).argmin() #plant attached to i/o points
      cor_path = correctedPath(pi, po, s_tr[plant])      
      toolPath = np.hstack([toolPath,cor_path])
      if k < (len(io_points[0])/2-1):
         toolPath = np.hstack([toolPath, dense_boustro[:,indexes[2*k+1]:indexes[2*k+2]]])

   toolPath = np.hstack([toolPath, dense_boustro[:,indexes[2*k+1]:]])
   toolPath = rdp(toolPath.T, eps_toolpath)

   if logger:
      renderPath(mask, toolPath.T, logger.makePath("toolpath"))

   return toolPath.T

   

def renderPath(mask, path, filepath):
   stp = np.round(path.T, 0).reshape((-1,1,2)).astype(np.int32)
   cv2.polylines(mask, [stp], False, [145,235,229],8)
   cv2.imwrite(filepath, mask)


def saveToSVG(path, backgroundImage, width, height, filepath):
   doc = svg.SVGDocument(filepath, width, height)
   doc.addImage(backgroundImage, 0, 0, width, height)
   if len(path[0]) > 1:
      doc.addPath(path[0], path[1])
   doc.close()

   
def fillWithPoints(xy, numberOfPoints):
   ts = np.linspace(0, len(xy[0]), num=len(xy[0]), endpoint=True)
   nts = np.linspace(0, len(xy[0]), num=numberOfPoints, endpoint=True)
   fx = np.interp(nts, ts, xy[0])
   fy = np.interp(nts, ts, xy[1])
   return np.array([fx, fy])


def pointLineDistance(point, start, end):
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
        d = pointLineDistance(points[i], points[0], points[-1])
        if d > dmax:
            index = i
            dmax = d
    if dmax >= epsilon:
        res1 = rdp(points[:index+1], epsilon)
        res2 = rdp(points[index:], epsilon)
        return np.vstack([res1[:-1],res2])
    else:
        return np.vstack([points[0], points[-1]])


 
def correctedPath(pi,po,tr,Nfp=200):
   """
   Substitute path passing through plants by shortest contour connecting i/o points 
   """
   longtr = fillWithPoints(tr.T, Nfp) 
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


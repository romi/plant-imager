import numpy as np
import cv2
from lettucethink import path
import lettucethink.cv as lcv


def corrected_path(pi, po, tr, Nfp=200):
   """
   Substitute path passing through plants by shortest contour connecting i/o points 
   """
   longtr = path.fill_with_points(tr.T, Nfp) 
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


def compute_modified_boustrophedon(mask, toolsize, workspace,
                                   eps_contours=5, eps_toolpath=5,
                                   numFillPoints=5000):

   # Compute boustrophedon ignoring the plants. All coordinates are in
   # image pixels. The boustrophedon start at y=0 (top of image),
   # because that is where the CNC arm is when the image is taken.
   boustro = path.make_boustrophedon(0, 0, toolsize, workspace.height - 1, workspace.width)

   # Detect i/o points of paths passing through plants
   dense_boustro = path.fill_with_points(boustro, numFillPoints)
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
      s_tr.append(path.rdp(contour, eps_contours))
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
   toolpath = path.rdp(toolpath.T, eps_toolpath)

#   if log.is_enabled():
#      path.render_path(mask, toolpath.T, log.make_image_path("toolpath"))

   return toolpath.T

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
import cv2
import numpy as np
from matplotlib import pyplot as plt
import sys
from lettucethink import log

def rotate_and_crop(image, workspace):
   (ih, iw) = image.shape[:2]
   M = cv2.getRotationMatrix2D((workspace.x0, ih-workspace.y0), workspace.theta, 1)
   rotated = cv2.warpAffine(image, M, (iw, ih))
   log.store_image("rotated", rotated)

   cropped = image[ih - workspace.y0 - workspace.height:ih-workspace.y0,
                workspace.x0:workspace.x0 + workspace.width]
   log.store_image("cropped", cropped)
   return cropped


# Calculates the plantmask of the image given as input.
def calculate_plant_mask(image, toolsize, bilf=[11, 5, 17], morpho_it=[10, 5]):

   ExG = calculate_excess_green(image)
   M = ExG.max()
   m = ExG.min()
        
   # Scale all values to the range (0, 255)
   ExGNorm = (255 * (ExG - m) / (M - m)).astype(np.uint8)
        
   # Smooth the image using a bilateral filter
   ExGNorm = cv2.bilateralFilter(ExGNorm, bilf[0], bilf[1], bilf[2])

   log.store_image("exgnorm", ExGNorm)
        
   # Calculte the mask using Otsu's method (see
   # https://docs.opencv.org/3.0-beta/doc/py_tutorials/py_imgproc/py_thresholding/py_thresholding.html)
   th, mask = cv2.threshold(ExGNorm, 0, 255, cv2.THRESH_OTSU)

   log.store_image("mask1", mask)

   if log.is_enabled():
      plt.subplot(1, 5, 1), plt.imshow(image)
      plt.title("image"), plt.xticks([]), plt.yticks([])
        
      plt.subplot(1, 5, 2), plt.imshow(ExG, 'gray')
      plt.title("ExG"), plt.xticks([]), plt.yticks([])
        
      plt.subplot(1, 5, 3), plt.imshow(ExGNorm, 'gray')
      plt.title("filtered"), plt.xticks([]), plt.yticks([])
        
      plt.subplot(1, 5, 4), plt.hist(ExGNorm.ravel(), 256), plt.axvline(x=th, color="red", linewidth=0.1)
      plt.title("histo"), plt.xticks([]), plt.yticks([])
      
      plt.subplot(1, 5, 5), plt.imshow(mask, 'gray')
      plt.title("mask"), plt.xticks([]), plt.yticks([])
      
      plt.savefig(log.make_image_path("plot"), dpi=300)

   # The kernel is a cross:
   #   0 1 0
   #   1 1 1
   #   0 1 0
   kernel = np.ones((3, 3)).astype(np.uint8)
   kernel[[0, 0, 2, 2], [0, 2, 2, 0]] = 0

   # Reduce the surfaces, to filter small one out.
   # See https://docs.opencv.org/3.0-beta/doc/py_tutorials/py_imgproc/py_morphological_ops/py_morphological_ops.html
   print("morphologyEx: %d" % morpho_it[0])
   #mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=morpho_it[0])
   mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=20)
   log.store_image("mask2", mask)

   # Increase the remaining surfaces.
   mask = cv2.dilate(mask, kernel=kernel, iterations=morpho_it[1])
   log.store_image("mask3", mask)

   # Invert the mask and calculate the distance to the closest black pixel.  
   # See https://docs.opencv.org/2.4.8/modules/imgproc/doc/miscellaneous_transformations.html#distancetransform
   dist = cv2.distanceTransform(255 - (mask.astype(np.uint8)),
                                cv2.DIST_L2,
                                cv2.DIST_MASK_PRECISE)
   # Turn white all the black pixels that are less than half the
   # toolsize away from a white (=plant) pixel
   mask = 255 * (1 - (dist > toolsize/2)).astype(np.uint8)

   log.store_image("mask", mask)
         
   return mask


def calculate_excess_green(colorImage):
   # ExcessGreen (ExG) is defined for a given pixel as
   #   ExG=2g-r-b
   # with r, g, b the normalized red, green and blue components:
   #   r = Rn/(Rn+Gn+Bn)   
   #   g = Gn/(Rn+Gn+Bn)   
   #   b = Bn/(Rn+Gn+Bn)
   # 
   # Rn, Gn, Bn are the normalized color values in the range of (0, 1):
   #   Rn=R/max(R), Gn=G/max(G), ...
   #
   # R, G, B are the non-normalized or "raw" color values.
   #
   # 2g-r-b can be rewritten as
   # 2g-r-b = 2G/(R+G+B) - G/(R+G+B) - B/(R+G+B)
   #        = (2G-R-B) / (R+G+B)
   #        = (3G-(R+G+B)) / (R+G+B)
   #        = 3G/(R+G+B) - 1
   #
   # See also Meyer & Neto, Verification of color vegetation indices
   # for automated crop imaging applications,
   # https://www.agencia.cnptia.embrapa.br/Repositorio/sdarticle_000fjtyeioo02wyiv80sq98yqrwt3ej2.pdf
   
   # Ms = [Bm, Gm, Rm], with Bm=max(B(i,j)), Gm=max(G(i,j)), ... 
   Ms = np.max(colorImage, axis = (0, 1)).astype(np.float) 

   # normalizedImage: all rgb values in the range (0, 1):
   #    e(i,j) = [Bn(i,j), Gn(i,j), Rn(i,j)]
   # with Bn(i,j) = B(i,j)/Bm, ...
   normalizedImage = colorImage / Ms

   # L is a 2-dimensional array with L(i,j) = Bn(i,j) + Gn(i,j) + Rn(i,j) 
   L = normalizedImage.sum(axis = 2)

   # ExG is a 2-dimensional array with
   #   e(i,j) = 3 * Gn(i,j) / L(i,j) - 1
   #   e(i,j) = 3 * Gn(i,j) / (Bn(i,j) + Gn(i,j) + Rn(i,j)) - 1
   ExG = 3 * normalizedImage[:, :, 1] / L - 1
   ExG = np.nan_to_num(ExG) # handle division by zero if L(i,j)=0 
      
   return ExG


def get_plant_contours(mask):
   # See https://docs.opencv.org/3.0.0/d4/d73/tutorial_py_contours_begin.html
   im, contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
   # Reorganise the arrays + remove contours with less than 10 points???
   contours = [np.vstack([ci[:,0], ci[:,0][0]]) for ci in contours if (len(ci) > 10)]
   return contours


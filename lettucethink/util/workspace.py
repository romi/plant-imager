import numpy as np

class Workspace(object):
   # (x0,y0) are the pixel coordinates of the origin of the CNC in the
   # topcam image.
   #
   # theta is the angle, in degrees, over which the image should
   # rotated (around x0,y0) to align the topcam image withe frame of
   # the rover topcam image. Only a rotation around the z-axis is
   # considered for now.
   #
   # width_px and height_px are the width and height of the workspace,
   # measured in pixels, as seen in the topcam image.
   # 
   # width_mm, height_mm are the width and the height of the real
   # workspace, measured in millimeters.
   def __init__(self, theta,
                x0, y0,
                width_px, height_px,
                width_mm, height_mm):
      self.theta = theta
      self.x0 = x0
      self.y0 = y0
      self.width = width_px
      self.height = height_px
      self.realWidth = width_mm
      self.realHeight = height_mm
      radians = np.radians(theta)
      self.c = np.cos(radians)
      self.s = np.sin(radians)

   # Converts a point in the topcam image (the original image, not the
   # cropped and rotated image) to the coordinate in the CNC's
   # workspace in millimeters.
   def convertImagePoint(self, x, y):
      x -= self.x0
      y -= self.y0
      x = self.px2mm(self.c * x - self.s * y)
      y = self.px2mm(self.s * x + self.c * y)
      return x, y
   
   def px2mm(self, x):
      return self.realWidth * x / self.width

   def mm2px(self, x):
      return self.width * x / self.realWidth

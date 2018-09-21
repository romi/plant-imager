import cv2
import sys
import os
from lettucethink import log, workspace, path, cv, urlcam

# main
workspace = workspace.Workspace(-2.1, 958, 546, 1318, 1336, 660, 660)

log.enable()

# If a filename was passed on the command line then load the image
# from the file. Otherwise grab the image from the topcam.
if len(sys.argv) == 1:
   print("Grabbing topcam image" )
   log.set_root("static/workspace")
   camera = urlcam.Camera("http://10.20.30.33:10000/image.jpg")
   image = camera.grab()
   log.store_image("topcam", image)

else:
   inputpath = sys.argv[1]
   print("Loading %s" % inputpath)
   image = cv2.imread(inputpath)
   (dirname, filename) = os.path.split(inputpath)
   (name, ext) = os.path.splitext(filename)   
   s = os.path.join(dirname, name)
   log.set_root("%s.d" % s)
   log.store_image("topcam", image)

   
# Here's the real processing: 
cropped = cv.rotate_and_crop(image, workspace)
mask = cv.calculate_plant_mask(cropped, 180, morpho_it=[5, 2])
path = path.compute_modified_boustrophedon(mask, workspace.mm2px(80), workspace)


# Output the results to an SVG file for further inspection
if len(path[0]) > 1:
   filepath = log.make_file_path("toolpath", "svg")
   bgimage = log.get_last_path("cropped")
   height = mask.shape[0]
   width = mask.shape[1]
   path.save_to_svg(path, bgimage, width, height, filepath)
   print("Path saved in %s" % path)
else:
   print("Empty path")


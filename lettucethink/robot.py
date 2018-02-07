#!/usr/bin/python
import cnc
import bracket
import cam_ds
import utils as ut

class Robot(object):
    def __init__(self, scandir, x=0, y=0, z=0, pan=0, tilt=0):
        self.cnc     = cnc.CNC(x, y, z, homing=True)
        self.bracket = bracket.Bracket(pan, tilt)
        self.cam     = cam_ds.Camera()
        self.scandir = scandir
        self.files   = [] #not sure it belongs there  

    def scanAt(self, x, y, z, pan, tilt, i, files):
        cnc.move_to(x, y, z)
        bracket.move_to(pan, tilt)
        time.sleep(2)
        rgb = "rgb-%03d.png"%i
        depth = "depth-%03d.png"%i
        grab_images(scandir + rgb,
                    scandir + depth)
        self.files.append({"href": "scan/" + rgb,
                      "name": rgb})
        self.files.append({"href": "scan/" + depth,
                      "name": depth})
        return

    def circularscan(self, xc, yc, zc, r, nc):
       self.files = []    
       x, y, pan = ut.circular_coordinates(xc, yc, r, nc)
       for i in range(0, nc):
         self.scanAt(x[i], y[i], zc, pan[i], self.bracket.tilt, i)
       cnc.move_to(x[0], y[0], zc)
       bracket.move_to(0, selftilt)
       self.files.append(ut.createArchive(self.files))
       
    def get_position(self):
       return {'x': self.cnc.x, 'y': self.cnc.y, 'z': self.cnc.z, 'pan': self.bracket.pan, 'tilt': self.bracket.tilt }



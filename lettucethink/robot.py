#!/usr/bin/env python3
from hardware import cartesian_arm, rotation_unit, camera
from motion_planning import scanpath  
import utils as ut
import time
import numpy as np
import os

class Robot(object):
    def __init__(self, scandir, x=0, y=0, z=0, pan=0, tilt=0, homing=True):
        self.cnc     = cartesian_arm.CNC(port="/dev/ttyUSB0",x=x, y=y, z=z,homing=homing)
        self.bracket = XL430_gimbal.XL430()
        self.cam     = camera.Camera()
        self.scandir = scandir
        self.t0      = tilt

    def scan_at(self, x, y, z, pan, tilt, i, dt=2):
        self.bracket.moveto(pan, tilt)
        self.cnc.moveto(x, y, z)
        time.sleep(dt)
        self.cam.grab_datas(self.scandir, i)
        return

    def circular_scan(self, xc, yc, zc, r, nc, svg="all.zip"):
        self.bracket.start()
        self.files = []
        traj=[]
        x, y, pan = scanpath.circle(xc, yc, r, nc)
        pan=360-pan
        
        for i in range(0, nc):
           xi, yi, zi = self.xyz_clamp(x[i], y[i], zc)
           #pi, ti  = self.pantilt_clamp(pan[i], self.t0)
           pi,ti=pan[i], self.t0
           print pi 
           traj.append([xi,yi,zi,pi,ti])
           self.scan_at(xi, yi, zi, pi, ti, i)
       
        self.cnc.moveto(x[0], y[0], zc)
        self.bracket.moveto(0, self.t0)
        np.save(self.scandir+"traj", np.asarray(traj))
        ut.createArchive(self.scandir, svg)
 
    def get_position(self):
        return {'x': self.cnc.x, 'y': self.cnc.y, 'z': self.cnc.z, 'pan': self.bracket.pan, 'tilt': self.bracket.tilt }

    def xyz_clamp(self, x, y, z):
        return ut.clamp(x, self.cnc.x_lims), ut.clamp(y, self.cnc.y_lims), ut.clamp(z, self.cnc.z_lims)

    def pantilt_clamp(self, pan, tilt):
        return ut.clamp(pan, self.bracket.pan_lims), ut.clamp(tilt, self.bracket.tilt_lims)

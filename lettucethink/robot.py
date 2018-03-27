#!/usr/bin/env python3
from hardware import grbl_cnc, XL430_gimbal, ds_camera
from motion_planning import scanpath  
import utils as ut
import time
import numpy as np
import os

class Robot(object):
    def __init__(self, cnc_port="/dev/ttyUSB1", gimbal_port="/dev/ttyUSB0", scandir=".", x=0, y=0, z=0, pan=0, tilt=0, homing=True):
        self.cnc     = grbl_cnc.GrblCNC(cnc_port,x=x, y=y, z=z,homing=homing)
        self.bracket = XL430_gimbal.XL430(gimbal_port)
        self.cam     = ds_camera.DSCamera()
        self.scandir = scandir
        self.t0      = tilt

    def start(self):
        self.cnc.start()
        self.bracket.start()        
        self.cam.start()
        
    def scan_at(self, x, y, z, pan, tilt, i, dt=2):
        self.bracket.move_to(pan, tilt)
        self.cnc.move_to(x, y, z)
        time.sleep(dt)
        self.cam.grab_write_all(self.scandir, str(i).zfill(3))
        return

    def circular_scan(self, xc, yc, zc, r, nc, svg="all.zip"):
        self.bracket.start()
        self.files = []
        traj=[]
        x, y, pan = scanpath.circle(xc, yc, r, nc)
        x=x[::-1]
        y=y[::-1]
        pan=pan
        
        for i in range(0, nc):
           xi, yi, zi = self.xyz_clamp(x[i], y[i], zc)
           #pi, ti  = self.pantilt_clamp(pan[i], self.t0)
           pi,ti=pan[i], self.t0
           #print(pi)
           traj.append([xi,yi,zi,pi,ti])
           self.scan_at(xi, yi, zi, pi, ti, i)
       
        self.cnc.move_to(x[0], y[0], zc)
        self.bracket.move_to(0, self.t0)
        np.save(self.scandir+"traj", np.asarray(traj))
        ut.createArchive(self.scandir, svg)
 
    def get_position(self):
        return {'x': self.cnc.x, 'y': self.cnc.y, 'z': self.cnc.z, 'pan': self.bracket.pan, 'tilt': self.bracket.tilt }

    def xyz_clamp(self, x, y, z):
        return ut.clamp(x, self.cnc.x_lims), ut.clamp(y, self.cnc.y_lims), ut.clamp(z, self.cnc.z_lims)

    def pantilt_clamp(self, pan, tilt):
        return ut.clamp(pan, self.bracket.pan_lims), ut.clamp(tilt, self.bracket.tilt_lims)

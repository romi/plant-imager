#!/usr/bin/env python3
from lettucethink.hardware import grbl_cnc, XL430_gimbal, ds_camera, gp2_camera
from lettucethink.motion_planning import scanpath  
import utils as ut
import time
import numpy as np
import os

class Robot(object):
    @staticmethod
    def create_robot_grbl_ds_xl430(cnc_port="/dev/ttyUSB0",
                                   gimbal_port="/dev/ttyUSB1",
                   homing=True, scan_dir="scan"):
        """
        Creates a robot with:
        - GRBL CNC
        - DepthSense Camera
        - XL430 Gimbal
        :param cnc_port: CNC Port (/dev/ttyUSB0 by default)
        :param gimbal_port: CNC Port (/dev/ttyUSB1 by default)
        :param homing: whether to perform homing or not on the CNC
        """
        robot = Robot()
        robot.cnc     = grbl_cnc.GrblCNC(cnc_port, homing=homing)
        robot.bracket = XL430_gimbal.XL430(gimbal_port)
        robot.cam     = ds_camera.DSCamera()
        robot.scan_dir = scan_dir
        return robot

    @staticmethod
    def create_robot_grbl_dshd_xl430(cnc_port="/dev/ttyUSB0",
                                   gimbal_port="/dev/ttyUSB1",
                   homing=True, scan_dir="scan"):
        """
        Creates a robot with:
        - GRBL CNC
        - DepthSense Camera in HD mode
        - XL430 Gimbal
        :param cnc_port: CNC Port (/dev/ttyUSB0 by default)
        :param gimbal_port: CNC Port (/dev/ttyUSB1 by default)
        :param homing: whether to perform homing or not on the CNC
        """
        robot = Robot()
        robot.cnc     = grbl_cnc.GrblCNC(cnc_port, homing=homing)
        robot.bracket = XL430_gimbal.XL430(gimbal_port)
        robot.cam     = ds_camera.DSCamera("hd")
        robot.scan_dir = scan_dir
        return robot


    
    @staticmethod
    def create_robot_grbl_gp2_xl430(cnc_port="/dev/ttyUSB0",
                                   gimbal_port="/dev/ttyUSB1",
                                   scan_dir="scan",
                   homing=True):
        """
        Creates a robot with:
        - GRBL CNC
        - Gphoto2 Camera
        - XL430 Gimbal
        :param cnc_port: CNC Port (/dev/ttyUSB0 by default)
        :param gimbal_port: CNC Port (/dev/ttyUSB1 by default)
        :param homing: whether to perform homing or not on the CNC
        """
        robot = Robot()
        robot.cnc     = grbl_cnc.GrblCNC(cnc_port, homing=homing)
        robot.bracket = XL430_gimbal.XL430(gimbal_port)
        robot.cam     = gp2_camera.GP2Camera()
        robot.scan_dir = scan_dir
        return robot

    def __init__(self):
        self.cnc = None
        self.bracket = None
        self.cam = None
        self.has_started = False
        self.t0 = 0
        self.is_busy = False

    def start(self):
        """
        Starts the scanner, by starting cnc, bracket and camera.
        """
        if self.cnc is None:
            raise ValueError("CNC is not defined")
        if self.bracket is None:
            raise ValueError("Bracket is not defined")
        if self.cam is None:
            raise ValueError("Camera is not defined")
        self.cnc.start()
        self.bracket.start()        
        self.cam.start()
        self.has_started = True

    def stop(self):
        print("stopping cnc.")
        self.cnc.stop()
        print("stopping bracket.")
        self.bracket.stop()
        print("stopping cam.")
        self.cam.stop()
        
    def scan_at(self, x, y, z, pan, tilt, suffix="", wait_time=2):
        """
        Moves arm to position (x,y,z,pan,tilt) and acquire data from camera.
        :param x: position x
        :param y: position y
        :param z: position z
        :param pan: orientation pan
        :param tilt: orientation tilt
        :param suffix: will be added to the file name
        :param wait_time: time to wait after movement before taking the shot
        """
        if not self.has_started:
            raise RuntimeError("You must call self.start() before scanning")
        self.is_busy = True
        self.bracket.move_to(pan, tilt)
        self.cnc.move_to(x, y, z)
        time.sleep(wait_time)
        result = self.cam.grab_write_all(self.scan_dir, suffix)
        self.is_busy = False
        return self.cam.grab_write_all(self.scan_dir, suffix)

    def circular_scan(self, xc, yc, zc, r, nc, output_archive="all.zip", output_gif=None):
        """
        Scans along a circular path
        :param xc: center x
        :param yc: center y
        :param zc: center z
        :param r: radius
        :param nc: number of points
        :param output_archive: where to save zip file scan
        """
        self.bracket.start()
        self.files = []
        scan_file = open(self.scan_dir + "/scan.csv", mode = 'w') 
        header_string = "x\ty\tz\tpan\ttilt\t"
        for data in self.cam.available_data:
            header_string = header_string + data + "\t"
        header_string = header_string[:-1] + "\n" #Remove last tab
        scan_file.write(header_string)
        x, y, pan = scanpath.circle(xc, yc, r, nc)
        
        for i in range(0, nc):
            xi, yi, zi = self.xyz_clamp(x[i], y[i], zc)
            pi, ti = pan[i], self.t0
            res = self.scan_at(xi, yi, zi, pi, ti, str(i).zfill(3))
            d = self.get_position()
            line_string = str(d['x']) + "\t" + str(d['y']) + "\t" + str(d['z']) + '\t' + str(d['pan']) + '\t' + str(d['tilt']) + '\t'
            for re in res:
                line_string = line_string + re + '\t'
            line_string = line_string[:-1] + "\n"
            scan_file.write(line_string)
            self.files.extend(res)
        scan_file.close()
        self.files.append(self.scan_dir + "/scan.csv")

       
        self.bracket.move_to(0, self.t0)
        self.cnc.move_to(x[0], y[0], zc)

        if output_archive: ut.createArchive(self.files, output_archive)
        if output_gif: ut.createGif(self.files, "rgb", output_gif)
	return self.files
 
    def get_position(self):
        return {'x': self.cnc.x,
                'y': self.cnc.y,
                'z': self.cnc.z,
                'pan': self.bracket.get_pan(),
                'tilt': self.bracket.get_tilt()}

    def xyz_clamp(self, x, y, z):
        return ut.clamp(x, self.cnc.x_lims), ut.clamp(y, self.cnc.y_lims), ut.clamp(z, self.cnc.z_lims)

    def pantilt_clamp(self, pan, tilt):
        return ut.clamp(pan, self.bracket.pan_lims), ut.clamp(tilt, self.bracket.tilt_lims)

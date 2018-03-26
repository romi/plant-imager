#!/usr/bin/env python2
import gphoto2 as gp
import os
import cv2


class GP2Camera():
    '''
    Gphoto2 Camera object.
    ''' 

    def __init__(self):
        self.camera = gp.Camera()
        self.is_started = False

    def start(self):
        self.camera.init()
        cfg = self.camera.get_config()
        cmode = cfg.get_child_by_name("capturemode")
        cmode.set_value(cmode.get_choice(0)) # should put in single shot mode
        self.is_started = True

    def stop(self):
        self.camera.exit()
        self.is_started = False

    def grab(self):
        self.write_to_file("/tmp/frame.jpg")
        return cv2.imread("/tmp/frame.jpg")


    def write_to_file(self, target):
        file_path = self.camera.capture(0)
        camera_file = self.camera.file_get(file_path.folder, file_path.name, gp.GP_FILE_TYPE_NORMAL)
        gp.check_result(gp.gp_file_save(camera_file, target))

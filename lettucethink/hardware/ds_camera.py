#!/usr/bin/env python3
import pydepthsense as ds
import imageio
import tifffile
from enum import Enum


class DSCameraMode(Enum):
    depth = 1
    hd = 2

def singleton(class_):
    instances = {}
    def instance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]
    return instance

modes = {"depth", "hd"}
@singleton
class DSCamera():
    '''
    DepthSense Camera object.
    ''' 

    def __init__(self, mode="depth"):
        """
        Constructor. Must call start() before use
        """
        if mode not in modes:
            raise ValueError("Incorrect mode")
        self.mode = mode
        if (self.mode == "depth"):
            self.available_data = {"sync",
                    "uv",
                    "confidence",
                    "vertices_fp",
                    "vertices",
                    "rgb",
                    "depth" }
            self.default_data = "depth"
        elif (self.mode == "hd"):
            self.available_data = {"rgb_hd"}
            self.default_data = "rgb_hd"
        self.is_started = False

    def start(self):
        if self.is_started:
            return
        if (self.mode == "depth"):
            ds.start()
        elif (self.mode == "hd"):
            ds.start_HD()
        self.is_started = True

    def stop(self):
        if not self.is_started:
            return
        ds.stop()
        self.is_started = False

    def grab_write_all(self, folder, suffix, data=None):
        """
        Grabs all data in data and writes it to folder/x${suffix}.tif
        where x is the data name (in available_data) 
        """
        res = []
        if data is None:
            data = self.available_data
        for x in data:
            fname = folder +"/" + x + suffix + ".tif"
            res.append(fname)
            self.grab_write(fname, x)
        return res

    def grab_write(self, target, data=None):
        """
        Writes result as a tif image
        """
        if data is None:
            data = self.default_data
        res = self.grab(data)
        if data in ["rgb", "rgb_hd", "sync"]:
            res = res[:,:,::-1]
        tifffile.imsave(target, res)
        
        #imageio.imsave(target, res)
        return target

    def grab(self, data=None):
        """
        Grabs a single frame of data in a numpy array
        """
        assert(self.is_started)
        if data is None:
            data = self.default_data
        if data not in self.available_data:
            raise ValueError("Incorrect data type")

        if data == "sync":
            return ds.getSyncMap()
        elif data == "uv":
            return ds.getUVMap()
        elif data == "confidence":
            return ds.getConfidenceMap()
        elif data == "vertices_fp":
            return ds.getVerticesFP()
        elif data == "vertices":
            return ds.getVertices()
        elif data == "rgb":
            return ds.getColorMap()
        elif data == "depth":
            return ds.getDepthMap()
        elif data == "rgb_hd":
            return ds.getHDColorMap()

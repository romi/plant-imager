#!/usr/bin/python
import pydepthsense as ds
import cv2
import numpy as np
from enum import Enum

class DSCameraData(Enum):
    sync = 1
    uv = 2
    confidence = 3
    float_vertices = 4
    vertices = 4
    color = 5
    depth = 6
    color_hd = 7


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

@singleton
class DSCamera():
    '''
    DepthSense Camera object.
    ''' 

    def __init__(self, mode=DSCameraMode.depth):
        if not isinstance(mode, DSCameraMode):
            raise TypeError(data)
        self.mode = mode
        if (self.mode == DSCameraMode.depth):
            self.available_data = {DSCameraData.sync,
                    DSCameraData.uv,
                    DSCameraData.confidence,
                    DSCameraData.float_vertices,
                    DSCameraData.vertices,
                    DSCameraData.color,
                    DSCameraData.depth }
            self.default_data = DSCameraData.depth
        elif (self.mode == DSCameraMode.depth):
            self.available_data = {DSCameraData.color_hd}
            self.default_data = DSCameraData.color_hd
        self.is_started = False

    def start(self):
        if (self.mode == DSCameraMode.depth):
            ds.start()
        elif (self.mode == DSCameraMode.depth):
            ds.start_HD()
        self.is_started = True

    def stop(self):
        if not self.is_started:
            return
        ds.stop()
        self.is_started = False

    def grab(self, data=None):
        if data is None:
            data = self.default_data
        if not isinstance(data, DSCameraData):
            raise TypeError(data)
        if data not in self.available_data:
            raise ValueError(data)

        if data == DSCameraData.sync:
            return ds.getSyncMap()
        elif data == DSCameraData.uv:
            return ds.getUVMap()
        elif data == DSCameraData.confidence:
            return ds.getConfidenceMap()
        elif data == DSCameraData.float_vertices:
            return ds.getVertices()
        elif data == DSCameraData.color:
            return ds.getColorMap()
        elif data == DSCameraData.depth:
            return ds.getDepthMap()
        elif data == DSCameraData.color_hd:
            return ds.getHDColorMap()

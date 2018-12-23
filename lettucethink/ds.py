"""

    lettucethink-python - Python tools the LettuceThink robot

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
#!/usr/bin/env python3
import pydepthsense as depthsense
import imageio
import tifffile
from enum import Enum
from lettucethink import hal, error


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
class Camera(hal.Camera):
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
            self.available_views = ["sync",
                    "uv",
                    "confidence",
                    "vertices_fp",
                    "vertices",
                    "rgb",
                    "depth" ]
            self.default_data = "depth"
        elif (self.mode == "hd"):
            self.available_views = ["rgb_hd"]
            self.default_data = "rgb_hd"
        self.is_started = False

        
    def start(self):
        if self.is_started:
            return
        if (self.mode == "depth"):
            depthsense.start()
        elif (self.mode == "hd"):
            depthsense.start_HD()
        self.is_started = True

        
    def stop(self):
        if not self.is_started:
            return
        depthsense.stop()
        self.is_started = False

        
    def get_views(self, index):
        return self.available_views

    
    def grab(self, view=None):
        """
        Grabs a single frame of data in a numpy array
        """
        assert(self.is_started)
        if view is None:
            view = self.default_view
        if view not in self.available_views:
            raise ValueError("Invalid view")

        if view == "sync":
            return depthsense.getSyncMap()
        elif view == "uv":
            return depthsense.getUVMap()
        elif view == "confidence":
            return depthsense.getConfidenceMap()
        elif view == "vertices_fp":
            return depthsense.getVerticesFP()
        elif view == "vertices":
            return depthsense.getVertices()
        elif view == "rgb":
            return depthsense.getColorMap()
        elif view == "depth":
            return depthsense.getDepthMap()
        elif view == "rgb_hd":
            return depthsense.getHDColorMap()
    

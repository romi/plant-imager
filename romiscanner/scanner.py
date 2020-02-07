"""

    romiscanner - Python tools for the ROMI 3D Scanner

    Copyright (C) 2018 Sony Computer Science Laboratories
    Authors: D. Colliaux, T. Wintz, P. Hanappe
  
    This file is part of romiscanner.

    romiscanner is free software: you can redistribute it
    and/or modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation, either
    version 3 of the License, or (at your option) any later version.

    romiscanner is distributed in the hope that it will be
    useful, but WITHOUT ANY WARRANTY; without even the implied
    warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with romiscanner.  If not, see
    <https://www.gnu.org/licenses/>.

"""    
import os
import numpy as np
import math
import time
from typing import List

from . import path
from .units import *
from .hal import *
from .vscan import VirtualScanner

from romidata.db import Fileset

class Scanner(AbstractScanner):
    def __init__(self, cnc: AbstractCNC,
                    gimbal: AbstractGimbal,
                    camera: AbstractCamera,
                    waiting_time: float=1.):
        super().__init__()
        self.cnc = cnc
        self.gimbal = gimbal
        self.camera = camera
        self.waiting_time = waiting_time # time to wait for stabilization after setting position

    def get_position(self) -> path.Pose:
        x,y,z = self.cnc.get_position()
        pan,tilt = self.gimbal.get_position()
        return path.Pose(x,y,z,pan,tilt)

    def set_position(self, pose: path.Pose) -> None:
        if self.cnc.async_enabled():
            self.cnc.moveto_async(pose.x, pose.y, pose.z)
            self.gimbal.moveto_async(pose.pan, pose.tilt)
            self.cnc.wait()
            self.gimbal.wait()
        else:
            self.cnc.moveto(x, y, z)
            self.gimbal.moveto(pose.pan, pose.tilt)
        time.wait(self.waiting_time)

    def grab(self, idx: int, metadata: dict=None):
        return self.camera.grab(idx, metadata)

    def channels(self) -> List[str]:
        return self.camera.channels()

class ScannerFactory():
    """
    Builds a scanner object from a config dictionary read
    in the json file.

    For a virtual scanner:
    ---
    ```
    {
        "type" : "virtual",
        "kwargs" : {
            "width" : WIDTH (int),
            "height" : HEIGHT (int),
            "focal" : FOCAL (float),
            "host" : "99.99.99.99" (str, default=None),
            "port" : "5000" (str, default=None),
            "classes" : List[str]=[],
        },
        "object" : "object.obj",
        "background" : "background.hdr",
    }
    ```

    For a real scanner:
    ---
    """
    def parse_config(scanner_config: dict) -> hal.AbstractScanner:
        type = "hardware" if "type" not in scanner_config else scanner_config["type"]
        try:
            if type == "hardware":
                cnc_module = scanner_config["cnc"]["module"]
                cnc_kwargs = scanner_config["cnc"]["kwargs"]
                cnc_module = importlib.import_module(cnc_module)
                cnc = getattr(cnc_module, "CNC")(**cnc_kwargs)

                gimbal_module = scanner_config["gimbal"]["module"]
                gimbal_kwargs = scanner_config["gimbal"]["kwargs"]
                gimbal_module = importlib.import_module(gimbal_module)
                gimbal = getattr(gimbal_module, "Gimbal")(**gimbal_kwargs)

                camera_module = scanner_config["camera"]["module"]
                camera_kwargs = scanner_config["camera"]["kwargs"]
                camera_module = importlib.import_module(camera_module)
                camera = getattr(camera_module, "Camera")(**camera_kwargs)

                return Scanner(cnc, gimbal, camera)
            elif type == "virtual":
                scanner_kwargs = scanner_config["kwargs"]
                return VirtualScanner
            else:
                raise "Unknown scanner type %s, must be 'hardware' or 'virtual'"



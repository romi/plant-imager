#!/usr/bin/env python3
"""

    lettucethink-python - Python tools for the LettuceThink robot

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
from lettucethink import scan, dynamixel, grbl, sony, blgimbal, dynamixel
import getopt
import sys
import numpy as np
from sys import argv
import os

import datetime
import time
import json

cnc_port = "/dev/ttyUSB0"
gimbal_port = "/dev/ttyUSB1"

print("Connecting to gimbal")
gimbal = dynamixel.Gimbal(gimbal_port, baud_rate=57600, tilt0=3072)

print("Connecting to CNC")
cnc = grbl.CNC(cnc_port, homing=True)

print("Connecting to camera")
camera = sony.Camera("http://192.168.122.1:8080")

scanner = scan.Scanner(cnc, gimbal, camera)

print("Starting scan")
files = scanner.do_circular_scan(400, 400, 350, 12, tilt=np.pi/10)

print("Finished scan")
print(files)



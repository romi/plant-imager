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
from lettucethink import scan, dynamixel, grbl, cvcam
import getopt
import sys
from sys import argv
import os

import datetime
import time
import json

cnc_port = "/dev/ttyACM0"
gimbal_port = "/dev/ttyUSB0"

print("Connecting to gimbal")
gimbal = dynamixel.Gimbal(gimbal_port)

print("Connecting to CNC")
cnc = grbl.CNC(cnc_port, homing=True)

print("Connecting to camera")
camera = cvcam.Camera(0, 640, 480)

scanner = scan.Scanner(cnc, gimbal, camera, inverted=True)

print("Starting scan")
files = scanner.do_circular_scan(400, 400, 250, 6)
print("Finished scan")
print(files)



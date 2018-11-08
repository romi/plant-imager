#!/usr/bin/env python3
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



#!/usr/bin/env python3
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



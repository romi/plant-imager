#!/usr/bin/env python3
from lettucethink import scan, dynamixel, cnccontroller, gp2
import getopt
import sys
from sys import argv
import os

import datetime
import time
import json

cnc_port = "/dev/ttyUSB0"
gimbal_port = "/dev/ttyUSB1"

print("Connecting to gimbal")
gimbal = dynamixel.Gimbal(gimbal_port)

gimbal.set_position(0, 0)

print("Connecting to CNC")
cnc = cnccontroller.CNC(cnc_port, homing=True)

print("Connecting to camera")
camera = gp2.Camera()

scanner = scan.Scanner(cnc, gimbal, camera)

print("Starting scan")
files = scanner.do_circular_scan(400, 400, 350, 12)

print("Finished scan")
print(files)



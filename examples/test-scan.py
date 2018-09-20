#!/usr/bin/env python3
from lettucethink import scan, dynamixel, grbl, gp2
import math

def rad(a):
    return math.pi * a / 180

cnc_port = "/dev/ttyUSB0"
gimbal_port = "/dev/ttyUSB1"

print("Connecting to gimbal")
gimbal = dynamixel.Gimbal(gimbal_port)

print("Connecting to CNC")
cnc = grbl.CNC(cnc_port, homing=True)

print("Connecting to camera")
camera = gp2.Camera()

scanner = scan.Scanner(cnc, gimbal, camera)

print("Starting scan")
scanner.set_default_filetype("jpg")
scanner.do_circular_scan(400, 400, 350, 36, z=0, tilt=rad(10))
scanner.do_circular_scan(400, 400, 350, 36, z=-40, tilt=0)
scanner.do_circular_scan(400, 400, 350, 36, z=-80, tilt=rad(-3))

print("Finished scan")
print(scanner.get_scan_files())


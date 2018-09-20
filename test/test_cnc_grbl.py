#!/usr/bin/env python3

from lettucethink import grbl

dev = "/dev/ttyUSB0"

print("Opening connection to CNC on %s" % dev)
cnc = grbl.CNC(dev, homing=True)

print("Moving to 400, 400")
cnc.moveto(400, 400, 0)

print("Moving to 0, 0")
cnc.moveto(0, 0, 0)

print("Done")

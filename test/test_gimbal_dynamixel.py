#!/usr/bin/env python3

from lettucethink import dynamixel
import time
import math

def rad(a):
    return math.pi * a / 180

dev = "/dev/ttyUSB1"

print("Opening connection to gimbal on %s" % dev)
gimbal = dynamixel.Gimbal(dev, mode = "position")

print("Moving to position (0,0)")
gimbal.moveto(0, 0)
print(gimbal.get_position())
print("Moving to position (20,20)")
gimbal.moveto(rad(20), rad(20))
print(gimbal.get_position())
print("Moving to position (0,0)")
gimbal.moveto(0, 0)
print(gimbal.get_position())


print("Switching to velocity mode")
gimbal.set_mode("velocity")

print("Moving at speed (10,10)")
gimbal.moveat(10, 10)

print("Waiting for 1 seconds")
for i in range(10):
    print(gimbal.get_position())
    time.sleep(0.1)

print("Moving back")
gimbal.moveat(-10, -10)

print("Waiting for 1 seconds")
for i in range(10):
    print(gimbal.get_position())
    time.sleep(0.1)

print("Stopping")
gimbal.moveat(0, 0)

print("Done")

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

from lettucethink import dynamixel
import time
import math

def rad(a):
    return math.pi * a / 180

dev = "/dev/ttyUSB0"

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

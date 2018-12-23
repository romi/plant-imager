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


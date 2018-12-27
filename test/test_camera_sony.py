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

from lettucethink import sony
import time
import imageio

print("Opening camera")
camera = sony.Camera("http://10.0.2.227:10000")

print("Waiting 3 seconds")
time.sleep(3)   

print("Grabbing image")
image = camera.grab()

print("Writing image to test.jpg")
imageio.imwrite('test.jpg', image)

print("Done")

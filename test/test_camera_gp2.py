#!/usr/bin/env python3

from lettucethink import gp2
import time
import imageio

print("Opening camera")
camera = gp2.Camera()

print("Waiting 3 seconds")
time.sleep(3)   

print("Grabbing image")
image = camera.grab()

print("Writing image to test.jpg")
imageio.imwrite('test.jpg', image)

print("Done")

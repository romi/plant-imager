#!/usr/bin/env python3

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

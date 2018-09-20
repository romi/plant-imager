#!/usr/bin/env python3

from lettucethink import cvcam
import time
import imageio

id = 1
width = 640
height = 480

print("Opening camera with id %d" % id)
camera = cvcam.Camera(1, width, height)

print(camera.get_resolution())

print("Waiting 3 seconds")
time.sleep(3)   

print("Grabbing image")
image = camera.grab()
print(image.shape)

print("Writing image to test.jpg")
imageio.imwrite('test.jpg', image)

print("Done")

#!/usr/bin/python
import pydepthsense as ds
import cv2

class Camera(object):
    '''
    DepthSense camera
    ''' 
    def __init__(self):
       ds.initDepthSense()

    def grab_image(self, rgb, depth):
       im_rgb = ds.getColourMap()
       cv2.imwrite(rgb, im_rgb)       
       im_depth = ds.getDepthMap()
       cv2.imwrite(depth, im_depth)   


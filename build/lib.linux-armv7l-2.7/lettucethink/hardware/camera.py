#!/usr/bin/python
import pydepthsense as ds
import cv2
import numpy as np

grab_data={"sync"  : ds.getSyncMap,
          "uv"    : ds.getUVMap,
          "conf"  : ds.getConfidenceMap,
          "vertFP": ds.getVerticesFP,
          "rgb"   : ds.getColorMap,
          "vert"  : ds.getVertices,
          "depth" : ds.getDepthMap}

class Camera(object):
    '''
    DepthSense camera-suffix is usually index coded on 3 digits
    ''' 
    def __init__(self):
       ds.start()

    def grab_datas(self, svg, suffix=0,
                   datas=["sync", "uv", "conf", "vertFP",
                          "rgb", "vert","depth"], pics=True):
       for d in datas:
          res=grab_data[d]()
          if d in ["sync", "rgb"]:
              cv2.imwrite(svg+"%s-%03d.png"%(d,suffix), res.astype(np.uint8))
          elif d in ["conf", "depth", "vert"]:
              cv2.imwrite(svg+"%s-%03d.png"%(d,suffix), res.astype(np.uint16))
          else:
              np.save(svg+"%s-%03d"%(d,suffix), res)

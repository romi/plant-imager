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
           "depth" : ds.getDepthMap,
           "HD"    :  ds.getHDColorMap}

class Camera(object):
    '''
    DepthSense camera-suffix is usually index coded on 3 digits
    ''' 
    def __init__(self, mode="depth"):
       self.mode=mode  
       if   self.mode=="depth": ds.start()
       elif self.mode=="HD"   : ds.start_HD()

    def stop(self):
        ds.stop()

    def setMode(self, mode):
        if self.mode!=mode:
            ds.stop()
            if   mode=="depth": ds.start()
            elif mode=="HD"   : ds.start_HD()
            self.mode=mode
       
    def grab_datas(self, svg, suffix=0,
                   datas=["sync", "uv", "conf", "vertFP",
                          "rgb", "vert","depth"], pics=True):
       for d in datas:
          res=grab_data[d]()
          if d in ["sync", "rgb","HD"]:
              cv2.imwrite(svg+"%s-%03d.png"%(d,suffix), res.astype(np.uint8))
          elif d in ["conf", "depth", "vert"]:
              cv2.imwrite(svg+"%s-%03d.png"%(d,suffix), res.astype(np.uint16))
          else:
              np.save(svg+"%s-%03d"%(d,suffix), res)

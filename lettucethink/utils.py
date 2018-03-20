#!/usr/bin/python
import zipfile
import numpy as np
import os

def createArchive(scandir='scan/', svg="all.zip"):
    files=os.listdir(scandir)
    zf = zipfile.ZipFile(svg, mode = 'w')
    try:    
        for f in files:
           print "adding", f["name"]
           zf.write(scandir+f["name"])
    finally:
        zf.close()
        return {"href": svg, "name": svg}

def clamp(value, lims, scale=1):
    return int(scale*np.clip(value, lims[0], lims[1]))

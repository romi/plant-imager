#!/usr/bin/env python3
import zipfile
import numpy as np
import os

def createArchive(files, output_archive="all.zip"):
    zf = zipfile.ZipFile(svg, mode = 'w')
    try:    
        for f in files:
           print("adding", f)
           zf.write(scandir+f)
    finally:
        zf.close()
        return {"href": output_archive, "name": output_archive}

def clamp(value, lims, scale=1):
    return int(scale*np.clip(value, lims[0], lims[1]))

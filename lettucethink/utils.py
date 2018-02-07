#!/usr/bin/python
import zipfile
import numpy as np

def createArchive(files, scandir='static/scan/'):
    #TODO: allow for specific name for the archive 
    zf = zipfile.ZipFile(zipname, mode = 'w')
    try:
        for f in files:
            print "adding", scandir + f["name"]
            zf.write(scandir + f["name"])
    finally:
        zf.close()
        return {"href": scandir+"all.zip", "name": "all.zip"}

def clamp(value, lims, scale=1):
    return int(scale*np.clip(value, lims[0], lims[1]))

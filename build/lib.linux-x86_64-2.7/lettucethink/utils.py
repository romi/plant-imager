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

def circular_coordinates(cx, cy, R, N):
   alpha = np.linspace(0, 2 * np.pi, N + 1)
   pan = np.linspace(0, -360.0, N + 1)
   x = cx + R * np.cos(alpha)
   y = cy + R * np.sin(alpha)
   return x, y, pan

def squarescan(xs, ys, zs, d, ns):
    return []

def clamp(value, lims, scale=1):
    return int(scale*np.clip(value, lims[0], lims[1]))

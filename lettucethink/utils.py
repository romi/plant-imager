#!/usr/bin/env python3
import zipfile
import imageio
import numpy as np
import os

def createArchive(files, output_archive="all.zip"):
    zf = zipfile.ZipFile(output_archive, mode = 'w')
    try:    
        for f in files:
           print("adding", f)
           zf.write(f)
    finally:
        zf.close()
    return {"href": output_archive, "name": output_archive}

def createGif(files, data="rgb", output_gif):
    with imageio.get_writer(output_gif, mode='I',duration=1) as writer:
          for f in files:
              if f[:len(data)]==data: writer.append_data(imageio.imread(f))
                    

def clamp(value, lims, scale=1):
    return int(scale*np.clip(value, lims[0], lims[1]))

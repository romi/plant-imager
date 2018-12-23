"""

    lettucethink-python - Python tools the LettuceThink robot

    Copyright (C) 2018 Sony Computer Science Laboratories
    Authors: D. Colliaux, T. Wintz, P. Hanappe
  
    This file is part of lettucethink-python.

    lettucethink-python is free software: you can redistribute it
    and/or modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation, either
    version 3 of the License, or (at your option) any later version.

    lettucethink-python is distributed in the hope that it will be
    useful, but WITHOUT ANY WARRANTY; without even the implied
    warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with lettucethink-python.  If not, see
    <https://www.gnu.org/licenses/>.

"""    
#!/usr/bin/env python3
import zipfile
import imageio
import numpy as np

def create_archive(files, output_archive="all.zip"):
    zf = zipfile.ZipFile(output_archive, mode = 'w')
    try:    
        for f in files:
           print("adding", f)
           zf.write(f)
    finally:
        zf.close()
    return {"href": output_archive, "name": output_archive}


def create_gif(files, data="rgb", output_gif="rgb.gif"):
    with imageio.get_writer(output_gif, mode='I',duration=1) as writer:
          for f in files:
              if f[:len(data)]==data: writer.append_data(imageio.imread(f))
                    

def clamp(value, lims, scale=1):
    return int(scale*np.clip(value, lims[0], lims[1]))

        


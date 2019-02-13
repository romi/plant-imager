"""

    lettucethink-python - Python tools for the LettuceThink robot

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

from lettucethink import hal, utils, path
import os
import math
import time


def archive_scan(files, output="scan.zip"):
    utils.create_archive(files, output)
        
        
def animate_scan(files, output="scan.gif"):
    utils.create_gif(files, output)

    
class Scanner(object):
    def __init__(self, cnc, gimbal, camera, db, scan_id, inverted=False):
        self.cnc = cnc
        self.gimbal = gimbal
        self.camera = camera
        self.db = db
        self.scan_id = scan_id
        self.inverted=inverted
        self.scan_count = 0


    def get_position(self):
        x, y, z = self.cnc.get_position()
        pan, tilt = self.gimbal.get_position()
        return {'x': x, 'y': y, 'z': z,
                'pan': pan, 'tilt': tilt}
                          

    def do_circular_scan(self, xc, yc, radius, num_points, z=None, tilt=None, metadata=None):
        if z is None:
            x, y, z = self.cnc.get_position()
        if tilt is None:
            pan, tilt = self.gimbal.get_position()
        circle = path.circle(xc, yc, z, tilt, radius, num_points)
        return self.scan(circle, metadata=metadata)

        
    def scan(self, path, metadata=None):
        """
        Scans along a given path 
        :param path: list of 5-tuples (x,y,z,pan,tilt)
        """
        nc = len(path)

        for i in range(nc):
            (x, y, z, pan, tilt) = path[i]
            #x, y, z = self.xyz_clamp(x, y, z) TODO
            self.scan_at(x, y, z, pan, tilt)
            self.scan_count += 1

        self.gimbal.moveto(0, 0) # FIXME
        self.cnc.moveto(*path[0][0:3])

        # Create scan only if successful
        scan = self.db.create_scan(self.scan_id)
        if metadata is not None:
            scan.set_metadata(metadata)
        self.camera.store_data(scan)
        return scan
        
    
    def scan_at(self, x, y, z, pan, tilt, wait_time=1):
        """
        Moves arm to position (x,y,z,pan,tilt) and acquire data from camera.
        :param x: position x
        :param y: position y
        :param z: position z
        :param pan: orientation pan
        :param tilt: orientation tilt
        :param wait_time: time to wait after movement before taking the shot
        """
        self.is_busy = True
        if self.inverted:
            pan = (math.pi - pan) % (2*math.pi)
        if self.cnc.async_enabled():
            self.cnc.moveto_async(x, y, z)
            self.gimbal.moveto_async(pan, tilt)
            self.cnc.wait()
            self.gimbal.wait()
        else:
            self.cnc.moveto(x, y, z)
            self.gimbal.moveto(pan, tilt)

        time.sleep(wait_time)
        self.camera.grab(metadata={"pose": [x, y, z, pan, tilt]})
        self.is_busy = False

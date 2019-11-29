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
import numpy as np
import math
import time

def cnc_gimbal_circle(cnc, gimbal, center, radius, callback_begin=None, callback_end=None,rotation_speed=10):
    cnc.send_cmd("g0 y%i x%i"%(center[1], center[0] - radius))

    feed_rate = int(rotation_speed * radius * 2 * np.pi)
    print("feed_rate = %i"%feed_rate)

    gimbal_speed = gimbal.steps_per_turn * rotation_speed / 60
    print("gimbal_speed = %i"%gimbal_speed)

    angle = np.arctan2(0, radius)
    gimbal.moveto_async(angle, 0)

    cnc.wait()
    if callback_begin is not None:
        callback_begin()

    cnc.serial_port.write(("g2 x%i i%i F%i\n"%(center[0] - radius, radius, feed_rate)).encode())
    # gimbal.moveat(gimbal_speed, 0)

    time.sleep(0.1)
    while True:
        status = cnc.get_status()
        if status is None:
            continue
        if status['status'] == 'Idle':
            break
        else:
            x,y,z = status['position']
            angle = np.arctan2(y - center[1], x - center[0])
            gimbal.moveto_async(angle, 0)
        time.sleep(0.01)
    if callback_end is not None:
        callback_end()


def archive_scan(files, output="scan.zip"):
    utils.create_archive(files, output)
        
        
def animate_scan(files, output="scan.gif"):
    utils.create_gif(files, output)

    
class Scanner(object):
    def __init__(self, cnc, gimbal, camera, inverted=False):
        self.cnc = cnc
        self.gimbal = gimbal
        self.camera = camera
        self.inverted=inverted
        self.scan_count = 0


    def get_position(self):
        x, y, z = self.cnc.get_position()
        pan, tilt = self.gimbal.get_position()
        return {'x': x, 'y': y, 'z': z,
                'pan': pan, 'tilt': tilt}

    def set_path(self, path, mask=None):
        """
        Parameters
        __________
        path: list
            List of 5-tuples (x,y,z,pan,tilt) or
            4-tupls (x,y,z,pan) or 3-tuples (x,y,z)
        mask: list
            list of bools. If an item is set to True,
            the position is stored as a metadata of the corresponding
            image, else not. If set to None (default), all positions
            are stored.

        """
        self.path = path
        self.mask = mask

    def circular_video_scan(self, center, radius, metadata=None):
        self.cnc.home()
        cnc_gimbal_circle(self.cnc, self.gimbal, center, radius, callback_begin=self.camera.start_recording,
                            callback_end=self.camera.stop_recording)

        while True:
            try:
                data = self.camera.retrieve_original_images()[-1]
                break
            except:
                time.sleep(1)
                continue

        # Create scan only if successful
        scan = self.db.create_scan(self.scan_id)
        if metadata is not None:
            scan.set_metadata(metadata)
        fileset = scan.create_fileset("video")
        video_file = fileset.create_file(data['id'])
        video_file.write_raw(data['data']['video'].read(), 'mp4')
        if data['metadata'] is not None:
            video_file.set_metadata(data['metadata'])

        return scan
                          
        
    def scan(self):
        """
        Scans along a given path 
        """
        path = self.path
        nc = len(path)

        print(self.mask)

        for i in range(nc):
            #try:
            if self.mask is not None:
                mask = self.mask[i]
                assert(type(mask) == bool)
            else:
                mask = True
            try:
                (x, y, z, pan, tilt) = path[i]
            except:
                try:
                    (x, y, z, pan) = path[i]
                    tilt = None
                except:
                    (x, y, z) = path[i]
                    pan = None
                    tilt = None
            #x, y, z = self.xyz_clamp(x, y, z) TODO
            try:
               self.scan_at(x, y, z, pan, tilt, store_pose=mask)
            except:
               break        
            self.scan_count += 1

        if self.gimbal: self.gimbal.moveto(0, 0) # FIXME
        #self.cnc.moveto(*path[0][0:3])
        self.cnc.home()
        self.cnc.set_home()

    def store(self, fileset, metadata=None):
        self.camera.store(fileset)
        # Create scan only if successful
        if metadata is not None:
            fileset.scan.set_metadata(metadata)
        
    
    def scan_at(self, x, y, z, pan, tilt, store_pose=True, wait_time=1):
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
        # c_pan, c_tilt = self.gimbal.get_position()

        # if pan is None:
        #     pan = c_pan
        # if tilt is None:
        #     tilt = c_tilt

        if self.inverted:
            pan = (math.pi - pan) % (2*math.pi)
        if self.cnc.async_enabled():
            self.cnc.moveto_async(x, y, z)
            if self.gimbal and pan is not None and tilt is not None: self.gimbal.moveto_async(pan, tilt)
            self.cnc.wait()
            if self.gimbal: self.gimbal.wait()
        else:
            self.cnc.moveto(x, y, z)
            if self.gimbal: self.gimbal.moveto(pan, tilt)

        time.sleep(wait_time)
        if store_pose:
            print("storing_pose")
            self.camera.grab(metadata={"pose": [x, y, z, pan, tilt]})
        else:
            self.camera.grab()
        self.is_busy = False

if __name__ == "__main__":
    from lettucethink import grbl
    from lettucethink import blgimbal
    from lettucethink import sony
    from romidata import fsdb

    db = fsdb.FSDB("testdb")

    cnc = grbl.CNC(homing=False)
    gimbal = blgimbal.Gimbal('/dev/ttyACM1', has_tilt=False, zero_pan=145)
    cam = sony.Camera("192.168.122.1", "8080", video_camera=True)  
    scanner = Scanner(cnc, gimbal, cam, db, "test_scan_3")
    

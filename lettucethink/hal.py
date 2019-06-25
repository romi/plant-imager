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
#import tifffile
# import imageio
from romidata import io
import os

class CNC(object):
    def __init__(self):
        pass

    def start(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError
    
    def home(self):
        raise NotImplementedError
    
    def has_position_control(self):
        raise NotImplementedError
    
    def get_position(self):
        raise NotImplementedError
    
    def moveto(self, x, y, z):
        raise NotImplementedError
    
    def async_enabled(self):
        raise NotImplementedError
    
    def moveto_async(self, x, y, z):
        raise NotImplementedError
    
    def wait(self):
        raise NotImplementedError

    def has_velocity_control(self):
        raise NotImplementedError
    
    def get_velocity(self):
        raise NotImplementedError

    def moveat(self, vx, vy, vz):
        raise NotImplementedError

    def start_spindle(self):
        raise NotImplementedError

    def stop_spindle(self):
        raise NotImplementedError

    def run_path(self, xs, ys, z):
       for i in range(0, len(xs)):
           self.moveto(xs[i], ys[i], z)


TOOL_NONE = 0
TOOL_GIMBAL = 1
TOOL_ROTATINGHOE = 2

class Tool(object):
    def __init__(self, type):
        self.type = type
    
    def get_tooltype(self):
        self.type

        
class Gimbal(Tool):
    def __init__(self):
        Tool.__init__(TOOL_GIMBAL)
    
    def has_position_control(self):
        raise NotImplementedError
    
    def get_position(self):
        raise NotImplementedError
    
    def moveto(self, pan, tilt):
        raise NotImplementedError

    def async_enabled(self, x, y, z):
        raise NotImplementedError
    
    def moveto_async(self, pan, tilt):
        raise NotImplementedError

    def wait(self):
        raise NotImplementedError

    def has_velocity_control(self):
        raise NotImplementedError
    
    def get_velocity(self):
        raise NotImplementedError

    def moveat(self, vpan, vtilt):
        raise NotImplementedError

    
class Camera(object):
    def __init__(self):
        pass

    def start(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def grab(self, metadata=None):
        raise NotImplementedError

    def get_channels(self):
        raise NotImplementedError
    
    def store_data(self, scan):
        print(self.tmpdir)
        data = self.get_data()
        fileset = scan.get_fileset('images', create=True)
        for data_item in data:
            print(data_item)
            channels = self.get_channels()
            for c in channels.keys():
                if len(channels) == 1:
                    file_id = '%s' % (data_item['id'])
                else:
                    file_id = '%s-%s'%(c,data_item['id'])
                if not(self.tmpdir):
                    new_file = fileset.create_file(file_id)
                    io.write_image(new_file, data_item['data'][c])
                    if data_item['metadata'] is not None:
                       new_file.set_metadata(data_item['metadata'])
        if self.tmpdir: self.save_data(fileset)  
    
class GameController(object):
    def __init__(self):
        pass

    def set_callback(self, name, callback):
        raise NotImplementedError

    def handle_events(self):
        raise NotImplementedError



class MotorController(object):
    def __init__(self):
        pass

    def reset_encoders(self):
        raise NotImplementedError

    def moveat(self, velocity):
        raise NotImplementedError

    def set_wheel_velocity(self, wheel, velocity):
        ''' wheel 0 is left, wheel 1 is right '''
        raise NotImplementedError


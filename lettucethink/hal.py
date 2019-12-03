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
    def __init__(self, *args, **kwargs):
        self.description = {
            "args": args,
            "kwargs": kwargs
        }
        self.last_id = 0
        self.store_queue = []

    def start(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def grab(self, metadata=None):
        raise NotImplementedError

    def store(self, fileset, last_n=None):
        n = 0
        while last_n is None or n < last_n:
            try:
                data_item = self.store_queue.pop()
            except:
                break
            for c in data_item['data'].keys():
                self.__store_item(data_item, fileset, c)
            n += 1

    def __store_item(self, data_item, fileset, channel):
        f = fileset.create_file(self.format_id(data_item['id'], channel))
        f.set_metadata('shot_id', data_item['id'])
        f.set_metadata(data_item['metadata'])
        f.set_metadata('channel', channel)
        if channel == 'rgb':
            io.write_image(f, data_item['data']['rgb'])
        elif channel == 'segmentation':
            io.write_volume(f, data_item['data']['segmentation'])
        else:
            raise ValueError("Wrong argument (channel): %s"%channel)

    def channels(self):
        raise NotImplementedError

    def format_id(self, id, channel):
        return "%05d_%s"%(id, channel)

    def up_id(self):
        aux = self.last_id
        self.last_id += 1
        return aux


   
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


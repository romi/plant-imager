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
#import tifffile
import imageio
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

    def grab(self, view=None):
        raise NotImplementedError

    def get_views(self):
        raise NotImplementedError
    
    def store_views(self, dir, filetype, suffix=None):
        files = []
        for view in self.get_views():
            if suffix:
                filename = "%s-%s.%s" % (view, suffix, filetype)
            else:
                filename = "%s.%s" % (view, filetype)
            filepath = os.path.join(dir, filename)
            image = self.grab(view)
            #if filetype == "tif":
            #    tifffile.imsave(filepath, image)
            #else:
            imageio.imwrite(filepath, image)
            files.append(filepath)
        return files

    def store_views_db(self, scan, filetype, suffix=None):
        files = []
        for view in self.get_views():
            image = self.grab(view)
            fileset = scan.get_fileset("images")
            file = fileset.create_file("%s-%s" % (view, suffix))
            file.write_image(filetype, image)
            files.append(file)
        return files


    
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


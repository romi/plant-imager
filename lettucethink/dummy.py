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
from lettucethink import hal, log
import time
import imageio

class CNC(hal.CNC):
    '''
    CNC functionalities 
    TODO: enable workspace origin offset, motor seed configuration,...
    ''' 
    def __init__(self, port="/dev/ttyUSB0", baud_rate=115200, homing=False, 
                       x_lims=[0,800], y_lims=[0,800], z_lims=[-100,0]):
        self.x = 0
        self.y = 0
        self.z = 0 
        
    def start(self, homing=False):
        pass

    def stop(self):
        pass
    
    def home(self):
        self.x = 0
        self.y = 0
        self.z = 0 
            
    def has_position_control():
        return True
    
    def get_position(self):
        return self.x, self.y, self.z 

    def async_enabled(self):
        return True
                    
    def moveto(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z 
    
    def moveto_async(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z 
        
    def wait(self):
        pass
    
    def has_velocity_control():
        return False
    
    def start_spindle(self):
        pass
    
    def stop_spindle(self):
        pass


class Camera(hal.Camera):
    def __init__(self, path):
        self.path = path
        self.image = imageio.imread(self.path)

    def start(self):
        pass

    def stop(self):
        pass

    def grab(self, view=None):
        return self.image

    def get_views(self):
        return ["rgb"]
    
       

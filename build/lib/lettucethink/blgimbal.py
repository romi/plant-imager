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

import serial
import json
import time
import math
import numpy as np
from lettucethink import hal, error

ZERO_PAN = 0
ZERO_TILT = 0


# cmp() is no longer defined in Python3 (silly)
def cmp(a, b):
    return (a > b) - (a < b)

class Gimbal(hal.CNC):
    def __init__(self, port="/dev/ttyUSB0", has_tilt=True, steps_per_turn=360,
                zero_pan=0, zero_tilt=0):
        self.port = port
        self.status = "idle"
        self.p = [0, 0]
        self.v = [0, 0]
        self.serial_port = None
        self.zero_pan = zero_pan
        self.zero_tilt = zero_tilt
        self.has_tilt = has_tilt
        self.steps_per_turn = steps_per_turn
        self.start()

        
    def start(self):
        self.serial_port = serial.Serial(self.port, 115200)
        # TODO: read '#ready' ?
        # while self.serial_port.in_waiting == 0:
            # time.sleep(0.1)
        # self.serial_port.readline()
        self.update_status()

    def stop(self):
        if self.serial_port:
            self.serial_port.close()
            self.serial_port = None

        
    def has_position_control():
        return True

    
    def async_enabled(self):
        return True

    
    def get_position(self):
        self.update_status()
        return self.p

    
    def has_velocity_control():
        return True

    
    def get_velocity(self):
        self.update_status()
        return self.v
   
      
       
    def get_status(self):
        self.update_status()
        return self.status

    
    def moveat(self, vpan, vtilt):
        self.__send("x%d" % vpan)
        if self.has_tilt:
            self.__send("y%d" % vtilt)

        
    def set_target_pos(self, pan, tilt):
        self.__send("X%d" % (self.zero_pan + int(pan / 2 / math.pi * self.steps_per_turn)))
        if self.has_tilt:
            self.__send("Y%d" % (self.zero_tilt + int(tilt / 2 / math.pi * self.steps_per_turn)))


    def wait(self):
        time.sleep(0.1)   
        self.update_status()
        while self.status == "moving":
            time.sleep(0.1)   
            self.update_status()

        
    def moveto(self, pan, tilt):
        self.moveto_async(pan, tilt)
        # self.wait()
        
        
    def moveto_async(self, pan, tilt):
        self.set_target_pos(pan, tilt)
       
            
    def update_status(self):
        v = self.__send("v").decode('utf-8')
        p = self.__send("p").decode('utf-8')
        p = p.split(":")[-1].split(",")
        v = v.split(":")[-1].split(",")
        # print(p)
        self.p[0] = (int(p[0]) - self.zero_pan) / self.steps_per_turn * math.pi * 2
        self.p[1] = (int(p[1]) - self.zero_tilt) / self.steps_per_turn * math.pi * 2
        # print("p="+ str(self.p))
        self.v[0] = int(v[0])
        self.v[1] = int(v[1])
        if self.v[0] != 0 or self.v[1] != 0:
            self.status = "moving"
        else:
            self.status = "idle"
        
    def __send(self, s):
        if not self.serial_port:
            raise Error("CNC has not been started")
        self.serial_port.reset_input_buffer()
        r = False
        try:
            self.serial_port.write(bytes('%s\n' % s, 'utf-8'))
            time.sleep(0.01)   
            r = self.serial_port.readline()
        finally:
            pass # dummy statement to avoid empty 'finally' clause
        if r == False:
            print('cmd=%s: failed' % (s))
        return r;

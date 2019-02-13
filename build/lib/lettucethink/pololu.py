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
import time
import numpy as np
from lettucethink import hal


class Gimbal(hal.CNC):
    def __init__(self, port="/dev/ttyACM0", pan=0, tilt=0, pan_lims=[-360,360],tilt_lims=[-90,90],homing=True):
        self.port = port
        self.serial_port = serial.Serial(self.port, 9600)
        time.sleep(2)
        self.serial_port.flushInput()
        self.pan = pan 
        self.tilt = tilt
        self.pan_lims = pan_lims
        self.tilt_lims = tilt_lims
        self.set_acc(50)
        self.set_speed(50)
        self.set_mode(1)
        if homing: self.moveto(0,0)
        
    def has_position_control():
        return Trye
    
    def get_position(self):
        return self.pan, self.tilt
    
    def async_enabled(self, x, y, z):
        return False
    
    def moveto_async(self, x, y, z):
        raise NotImplementedError

    def wait(self):
        raise NotImplementedError # TODO

    def moveto(self, pan, tilt):
        self.send_cmd("p%s;t%s"%(int(10*pan), int(10*tilt)))
        self.pan  = pan
        self.tilt = tilt

    def has_velocity_control():
        return False

    def set_acc(self, acc):
        self.send_cmd("a%s"%(int(acc)))

    def set_speed(self, speed):
        self.send_cmd("s%s"%(int(speed)))

    def set_mode(self, mode):
        self.send_cmd("m%s"%(int(mode)))

    def send_cmd(self, cmd):
        print(cmd)
        self.serial_port.write(cmd+"\n")
        out = self.serial_port.readline()
        print(' : ' + out.strip())
        return out

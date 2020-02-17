"""

    romiscanner - Python tools for the ROMI 3D Scanner

    Copyright (C) 2018 Sony Computer Science Laboratories
    Authors: D. Colliaux, T. Wintz, P. Hanappe

    This file is part of romiscanner.

    romiscanner is free software: you can redistribute it
    and/or modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation, either
    version 3 of the License, or (at your option) any later version.

    romiscanner is distributed in the hope that it will be
    useful, but WITHOUT ANY WARRANTY; without even the implied
    warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with romiscanner.  If not, see
    <https://www.gnu.org/licenses/>.

"""
import serial
import atexit
import time

from romiscanner import hal
from .log import logger

class CNC(hal.AbstractCNC):
    '''
    CNC functionalities
    '''
    def __init__(self, port="/dev/ttyUSB0", baud_rate=115200, homing=True,
                       x_lims=[0,800], y_lims=[0,800], z_lims=[-100,0]):
        self.port = port
        self.baud_rate = baud_rate
        self.homing = homing
        self.x_lims = x_lims
        self.y_lims = y_lims
        self.z_lims = z_lims
        self.serial_port = None
        self.x = 0
        self.y = 0
        self.z = 0
        self.start(homing)
        atexit.register(self.stop)


    def start(self, homing=True):
        self.serial_port = serial.Serial(self.port, self.baud_rate, timeout=10)
        self.has_started = True
        self.serial_port.write("\r\n\r\n".encode())
        time.sleep(2)
        self.serial_port.flushInput()
        if self.homing:
            self.home()
        self.send_cmd("g90")
        self.send_cmd("g21")

    def stop(self):
        if (self.has_started):
            self.serial_port.close()

    def get_position(self):
        return self.x, self.y, self.z

    def async_enabled(self):
        return True

    def home(self):
        self.send_cmd("$H")
        #self.send_cmd("g28") #reaching workspace origin
        self.send_cmd("g92 x0 y0 z0")

    def moveto(self, x, y, z):
        self.moveto_async(x, y, z)
        self.wait()

    def moveto_async(self, x, y, z):
        self.send_cmd("g0 x%s y%s z%s" % (int(x), int(y), int(z)))
        self.x = int(x)
        self.y = int(y)
        self.z = int(z)
        time.sleep(0.1) # Add a little sleep between calls

    def wait(self):
        self.send_cmd("g4 p1")


    def send_cmd(self, cmd):
        self.serial_port.reset_input_buffer()
        logger.debug("%s -> cnc" % cmd)
        self.serial_port.write((cmd + "\n").encode())
        grbl_out = self.serial_port.readline()
        logger.debug("cnc -> %s" % grbl_out.strip())
        time.sleep(0.1)
        return grbl_out

    def get_status(self):
        self.serial_port.write("?".encode("utf-8"))
        try:
            res = self.serial_port.readline()
            res = res.decode("utf-8")
            res = res[1:-1]
            res = res.split('|')
            print(res)
            res_fmt = {}
            res_fmt['status'] = res[0]
            pos = res[1].split(':')[-1].split(',')
            pos = [-float(p) for p in pos] # why - ?
            res_fmt['position'] = pos
        except:
            return None
        return res_fmt

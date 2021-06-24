#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# plantimager - Python tools for the ROMI 3D Plant Imager
#
# Copyright (C) 2018 Sony Computer Science Laboratories
# Authors: D. Colliaux, T. Wintz, P. Hanappe
#
# This file is part of plantimager.
#
# plantimager is free software: you can redistribute it
# and/or modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# plantimager is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with plantimager.  If not, see
# <https://www.gnu.org/licenses/>.

"""Implementation of a class dedicated to controlling a Gimbal.

This Gimbal implementation is based on a custom built controller.
The gimbal is used to orient a camera by controlling _pan_ & _tilt_ orientations.
The control is done by a serial port that has to be defined.
Note that this module offer the ability to use one or two motors.
With one, you control the pan orientation, this is like turning your head left or right.
With two, you can also control the tilt, this is like looking up or down.
In conjunction with a 3-axis CNC, that gives a total of 5 degrees of freedom and thus the ability to scan the whole volume around the plant.

"""

import atexit
import time

import serial
from plantimager.error import Error
from plantimager.hal import AbstractGimbal


class Gimbal(AbstractGimbal):
    def __init__(self, port="/dev/ttyUSB0", has_tilt=True, steps_per_turn=360,
                 zero_pan=0, zero_tilt=0, invert_rotation=False):
        super().__init__()
        self.port = port
        self.status = "idle"
        self.p = [0, 0]
        self.v = [0, 0]
        self.serial_port = None
        self.zero_pan = zero_pan
        self.zero_tilt = zero_tilt
        self.has_tilt = has_tilt
        self.steps_per_turn = steps_per_turn
        self.invert_rotation = invert_rotation
        self.start()
        atexit.register(self.stop)

    def start(self):
        self.serial_port = serial.Serial(self.port, 115200, timeout=1)
        self.update_status()

    def stop(self):
        if self.serial_port:
            self.serial_port.close()
            self.serial_port = None

    def has_position_control(self):
        return True

    def async_enabled(self):
        return True

    def get_position(self):
        self.update_status()
        return self.p

    def get_status(self):
        self.update_status()
        return self.status

    def set_target_pos(self, pan, tilt):
        if self.invert_rotation:
            pan = -pan
        self.__send("X%d" % (self.zero_pan + int(pan / 360 * self.steps_per_turn)))
        if self.has_tilt:
            self.__send("Y%d" % (self.zero_tilt + int(tilt / 360 * self.steps_per_turn)))

    def wait(self):
        pass

    def moveto(self, pan, tilt):
        self.moveto_async(pan, tilt)
        self.wait()

    def moveto_async(self, pan, tilt):
        self.set_target_pos(pan, tilt)

    def update_status(self):
        p = self.__send("p").decode('utf-8')
        p = p.split(":")[-1].split(",")
        self.p[0] = (int(p[0]) - self.zero_pan) / self.steps_per_turn * 360
        self.p[1] = (int(p[1]) - self.zero_tilt) / self.steps_per_turn * 360

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
            pass  # dummy statement to avoid empty 'finally' clause
        if r == False:
            print('cmd=%s: failed' % (s))
        return r

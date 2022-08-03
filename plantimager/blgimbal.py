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

"""Implementation of a class dedicated to controlling a gimbal.

This gimbal implementation is based on a custom-built controller.
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
from plantimager.log import logger


class Gimbal(AbstractGimbal):
    """Custom-built gimbal controller.

    Attributes
    ----------
    port : str
        Serial port to use for communication with the CNC, `"/dev/ttyUSB0"` by default.
    status : str
        Describe the gimbal current status, "idle" or "moving".
    p : [float, float]
        Current pan and tilt positions.
    serial_port :serial.Serial
        The `Serial` instance used to send commands to the gimbal.
    zero_pan : float
        The angle, in degree, to use as zero for pan.
    zero_tilt : float
        The angle, in degree, to use as zero for tilt.
    has_tilt : bool
        Indicate if the gimbal has a tilt motor or just a pan motor.
    steps_per_turn : int
        Number of steps required to complete a full rotation.
    invert_rotation : bool
        Use it to invert the rotation of the motor.

    Examples
    --------
    >>> from plantimager.blgimbal import Gimbal
    >>> g = Gimbal("/dev/ttyACM1", has_tilt=False, invert_rotation=True)
    >>> g.status

    """

    def __init__(self, port="/dev/ttyUSB0", has_tilt=True, steps_per_turn=360,
                 zero_pan=0, zero_tilt=0, invert_rotation=False):
        super().__init__()
        self.port = port
        self.status = "idle"
        self.p = [0, 0]
        self.serial_port = None
        self.zero_pan = zero_pan
        self.zero_tilt = zero_tilt
        self.has_tilt = has_tilt
        self.steps_per_turn = steps_per_turn
        self.invert_rotation = invert_rotation
        self.start()
        atexit.register(self.stop)

    def start(self):
        """Start the serial connection with the custom board controlling the Gimbal."""
        self.serial_port = serial.Serial(self.port, 115200, timeout=1, write_timeout=3)
        self.update_status()
        return None

    def stop(self):
        """Stop the serial connection with the custom board controlling the Gimbal."""
        if self.serial_port:
            self.serial_port.close()
            self.serial_port = None
        return None

    def has_position_control(self) -> bool:
        return True

    def async_enabled(self) -> bool:
        return True

    def get_position(self) -> list:
        """Returns the pan & tilt positions of the Gimbal."""
        self.update_status()
        return self.p

    def get_status(self) -> str:
        """Returns the status of the custom board controlling the Gimbal."""
        self.update_status()
        return self.status

    def set_target_pos(self, pan, tilt):
        """Set a target position for pan & tilt.

        Parameters
        ----------
        pan : float
            The desired `pan` orientation.
        tilt : float
            The desired `tilt` orientation.
        """
        if self.invert_rotation:
            pan = -pan
        self.__send("X%d" % (self.zero_pan + int(pan / 360 * self.steps_per_turn)))
        if self.has_tilt:
            self.__send("Y%d" % (self.zero_tilt + int(tilt / 360 * self.steps_per_turn)))
        return None

    def wait(self):
        pass

    def moveto(self, pan, tilt):
        """Move to a target position for pan & tilt.

        Parameters
        ----------
        pan : float
            The desired `pan` orientation.
        tilt : float
            The desired `tilt` orientation.
        """
        self.moveto_async(pan, tilt)
        self.wait()
        return None

    def moveto_async(self, pan, tilt):
        """Asynchronous move to a target position for pan & tilt.

        Parameters
        ----------
        pan : float
            The desired `pan` orientation.
        tilt : float
            The desired `tilt` orientation.
        """
        self.set_target_pos(pan, tilt)
        return None

    def update_status(self):
        """Update the pan & tilt positions."""
        p = self.__send("p").decode('utf-8')
        logger.debug(f"Raw gimbal response: {p}")
        p = p.split(":")[-1].split(",")
        logger.debug(f"Gimbal response: pan={p[0]}, tilt={p[1]}")
        self.p[0] = (int(p[0]) - self.zero_pan) / self.steps_per_turn * 360
        self.p[1] = (int(p[1]) - self.zero_tilt) / self.steps_per_turn * 360
        return None

    def __send(self, s):
        """Send a command trough the serial port.

        Parameters
        ----------
        s : str
            The command to send to the custom board controlling the Gimbal.
        """
        if not self.serial_port:
            raise Error("Serial connection to gimbal has not been started yet!")
        self.serial_port.reset_input_buffer()
        r = False
        try:
            self.serial_port.write(bytes(f"{s}\n", 'utf-8'))
            time.sleep(0.01)
            r = self.serial_port.readline()
        finally:
            pass  # dummy statement to avoid empty 'finally' clause
        if r == False:
            logger.critical(f"Command failed: `{s}`!")
        return r

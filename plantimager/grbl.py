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

"""Implementation of a CNC module adapted to Grbl motherboard.

The CNC is used to move a multi-purpose arm.
It offers 3-axis of movements.

"""

import atexit
import time

import serial
from plantimager.hal import AbstractCNC
from plantimager.log import logger

#: Dictionary mapping the Grbl codes to their meaning and units.
GRBL_SETTINGS = {
    "$0": ("Step pulse", "microseconds"),
    "$1": ("Step idle delay", "milliseconds"),
    "$2": ("Step port invert", "mask"),
    "$3": ("Direction port invert", "mask"),
    "$4": ("Step enable invert", "boolean"),
    "$5": ("Limit pins invert", "boolean"),
    "$6": ("Probe pin invert", "boolean"),
    "$10": ("Status report", "mask"),
    "$11": ("Junction deviation", "mm"),
    "$12": ("Arc tolerance", "mm"),
    "$13": ("Report inches", "boolean"),
    "$20": ("Soft limits", "boolean"),
    "$21": ("Hard limits", "boolean"),
    "$22": ("Homing cycle", "boolean"),
    "$23": ("Homing dir invert", "mask"),
    "$24": ("Homing feed", "mm/min"),
    "$25": ("Homing seek", "mm/min"),
    "$26": ("Homing debounce", "milliseconds"),
    "$27": ("Homing pull-off", "mm"),
    "$30": ("Max spindle speed", "RPM"),
    "$31": ("Min spindle speed", "RPM"),
    "$32": ("Laser mode", "boolean"),
    "$100": ("X steps/mm", "steps/mm"),
    "$101": ("Y steps/mm", "steps/mm"),
    "$102": ("Z steps/mm", "steps/mm"),
    "$110": ("X Max rate", "mm/min"),
    "$111": ("Y Max rate", "mm/min"),
    "$112": ("Z Max rate", "mm/min"),
    "$120": ("X Acceleration", "mm/sec^2"),
    "$121": ("Y Acceleration", "mm/sec^2"),
    "$122": ("Z Acceleration", "mm/sec^2"),
    "$130": ("X Max travel", "mm"),
    "$131": ("Y Max travel", "mm"),
    "$132": ("Z Max travel", "mm")
}


class CNC(AbstractCNC):
    """CNC functionalities.

    Attributes
    ----------
    port : str
        Serial port to use for communication with the CNC.
    baud_rate : int
        Communication baudrate, should be 115200 for the Arduino UNO.
    homing : bool
        If `True`, axes homing will be performed upon CNC object instantiation [RECOMMENDED].
    x_lims : (int, int)
        The allowed range of X-axis positions.
    y_lims : (int, int)
        The allowed range of Y-axis positions.
    z_lims : (int, int)
        The allowed range of Z-axis positions.
    serial_port : serial.Serial
        The `Serial` instance used to send commands to the Grbl.
    x : int
        The current position, in millimeter, of the CNC arm on the X-axis.
    y : int
        The current position, in millimeter, of the CNC arm on the Y-axis.
    z : int
        The current position, in millimeter, of the CNC arm on the Z-axis.
    invert_x : bool
        If `True`, "mirror" the coordinates direction respectively to 0.
    invert_y : bool
        If `True`, "mirror" the coordinates direction respectively to 0.
    invert_z : bool
        If `True`, "mirror" the coordinates direction respectively to 0.

    References
    ----------
    http://linuxcnc.org/docs/html/gcode/g-code.html

    """

    def __init__(self, port="/dev/ttyUSB0", baud_rate=115200, homing=True, x_lims=None, y_lims=None, z_lims=None,
                 safe_start=True, invert_x=True, invert_y=True, invert_z=True):
        """Constructor.

        Parameters
        ----------
        port : str, optional
            Serial port to use for communication with the CNC, `"/dev/ttyUSB0"` by default.
        baud_rate : int, optional
            Communication baudrate, `115200` by default (should work for the Arduino UNO).
        homing : bool, optional
            If `True` (default), axes homing will be performed upon CNC object instantiation [RECOMMENDED].
        x_lims : (int, int), optional
            The allowed range of X-axis positions, if `None` (default) use the settings from Grbl ("$130", see GRBL_SETTINGS).
        y_lims : (int, int), optional
            The allowed range of Y-axis positions, if `None` (default) use the settings from Grbl ("$131", see GRBL_SETTINGS).
        z_lims : (int, int), optional
            The allowed range of Z-axis positions, if `None` (default) use the settings from Grbl ("$132", see GRBL_SETTINGS).
        invert_x : bool
            If `True` (default), "mirror" the coordinates direction respectively to 0.
        invert_y : bool
            If `True` (default), "mirror" the coordinates direction respectively to 0.
        invert_z : bool
            If `True` (default), "mirror" the coordinates direction respectively to 0.

        Examples
        --------
        >>> from plantimager.grbl import CNC
        >>> cnc = CNC("/dev/ttyACM0", x_lims=[0, 780], y_lims=[0, 780], z_lims=[0, 90])
        >>> cnc.moveto(200, 200, 50)  # move the CNC to this XYZ coordinate (in mm)
        >>> cnc.home()  # homing command (automatically called on startup)
        >>> cnc.moveto_async(200, 200, 50)
        >>> cnc.send_cmd("$$")  # send a Grbl command, here "$$"
        >>> cnc.print_grbl_settings()  # Get Grbl settings from the firmware
        >>> cnc.stop()  # close the serial connection

        """
        super().__init__()
        self.port = port
        self.baud_rate = baud_rate
        self.x_lims = x_lims
        self.y_lims = y_lims
        self.z_lims = z_lims
        self.invert_x = invert_x
        self.invert_y = invert_y
        self.invert_z = invert_z
        self.serial_port = None
        self.x = 0
        self.y = 0
        self.z = 0
        self.grbl_settings = None
        self._start(homing, safe_start)
        atexit.register(self.stop)

    def _check_axes_limits(self, axis_limits, grbl_limits, axis_name):
        """Make sure given `axe_limits` are within `grbl_limits` (firmware limits).

        Parameters
        ----------
        axis_limits : [float, float]
            Axis limits to use.
        grbl_limits : [float, float]
            Limits knwon to Grbl firmaware ("$130", "$131" & "$132" in ``GRBL_SETTINGS``)
        axis_name : str
            Name of the axis currently checked.

        See Also
        --------
        GRBL_SETTINGS

        Raises
        ------
        ValueError
            If given `axe_limits` do not respect `grbl_limits`.

        Examples
        --------
        >>> from plantimager.grbl import CNC
        >>> cnc = CNC("/dev/ttyACM0")
        >>> grbl = cnc.get_grbl_settings()
        >>> print(f"Grbl axes limits are: X=[0, {grbl['$130']}], Y=[0, {grbl['$131']}], Z=[0, {grbl['$132']}]")
        >>> wrong_cnc = CNC("/dev/ttyACM0", x_lims=[-1, 780], y_lims=[0, 780], z_lims=[0, 90])

        """
        try:
            assert axis_limits[0] >= grbl_limits[0] and axis_limits[1] <= grbl_limits[1]
        except AssertionError:
            msg = f"Given {axis_name}-axis limits are WRONG!\n"
            msg += f"Should be in '{grbl_limits[0]}:{grbl_limits[1]}', but got '{axis_limits[0]}:{axis_limits[1]}'!"
            raise ValueError(msg)
        return None

    def _start(self, homing=True, safe_start=True):
        """Start the serial connection with the Arduino & initialize the CNC (hardware).

        Parameters
        ----------
        homing : bool
            If ``True``, performs homing procedure.
        safe_start : bool
            If ``True``, check the object have been initialized with proper axes limits.

        References
        ----------
        http://linuxcnc.org/docs/html/gcode/g-code.html#gcode:g90-g91
        http://linuxcnc.org/docs/html/gcode/g-code.html#gcode:g20-g21

        """
        self.serial_port = serial.Serial(self.port, self.baud_rate, timeout=10)
        self.has_started = True
        self.serial_port.write("\r\n\r\n".encode())
        time.sleep(2)
        self.serial_port.flushInput()
        # Performs homing procedure if required:
        if homing:
            self.home()
        # Set to "absolute distance mode":
        self.send_cmd("g90")
        # Use millimeters for length units:
        self.send_cmd("g21")

        if safe_start:
            # Initialize axes limits with Grbl settings if not set, else check given settings:
            self.grbl_settings = self.get_grbl_settings()
            if self.x_lims is None:
                self.x_lims = [0, self.grbl_settings["$130"]]
            else:
                self._check_axes_limits(self.x_lims, [0, self.grbl_settings["$130"]], 'X')
            if self.y_lims is None:
                self.y_lims = [0, self.grbl_settings["$131"]]
            else:
                self._check_axes_limits(self.y_lims, [0, self.grbl_settings["$131"]], 'Y')
            if self.z_lims is None:
                self.z_lims = [0, self.grbl_settings["$132"]]
            else:
                self._check_axes_limits(self.z_lims, [0, self.grbl_settings["$132"]], 'Z')
        return None

    def stop(self):
        """Close the serial connection."""
        if (self.has_started):
            self.serial_port.close()
        return None

    def get_position(self):
        """Returns the x, y & z positions of the CNC."""
        return self.x, self.y, self.z

    def async_enabled(self):
        return True

    def home(self):
        """Performs axes homing procedure.

        References
        ----------
        https://github.com/gnea/grbl/wiki/Grbl-v1.1-Commands#h---run-homing-cycle
        http://linuxcnc.org/docs/html/gcode/g-code.html#gcode:g92

        """
        # Send Grbl homing command:
        self.send_cmd("$H")
        # self.send_cmd("g28") #reaching workspace origin
        # Set current position to [0, 0, 0] (origin)
        # Note that there is a 'homing pull-off' value ($27)!
        self.send_cmd("g92 x0 y0 z0")
        return None

    def _check_move(self, x, y, z):
        """ Make sure the `moveto` coordinates are within the axes limits."""
        try:
            assert self.x_lims[0] <= x <= self.x_lims[1]
        except AssertionError:
            raise ValueError("Move command coordinates is outside the x-limits!")
        try:
            assert self.y_lims[0] <= y <= self.y_lims[1]
        except AssertionError:
            raise ValueError("Move command coordinates is outside the y-limits!")
        try:
            assert self.z_lims[0] <= z <= self.z_lims[1]
        except AssertionError:
            raise ValueError("Move command coordinates is outside the z-limits!")
        return None

    def moveto(self, x, y, z):
        """Send a 'G0' move command and wait until reaching target XYZ position.

        Parameters
        ----------
        x : int
            The target position, in millimeters, along the X-axis.
        y : int
            The target position, in millimeters, along the Y-axis.
        z : int
            The target position, in millimeters, along the Z-axis.

        """
        self._check_move(x, y, z)
        self.moveto_async(x, y, z)
        self.wait()
        return None

    def moveto_async(self, x, y, z):
        """Send a non-blocking 'G0' move command to target XYZ position.

        Parameters
        ----------
        x : int
            The target position, in millimeters, along the X-axis.
        y : int
            The target position, in millimeters, along the Y-axis.
        z : int
            The target position, in millimeters, along the Z-axis.

        References
        ----------
        http://linuxcnc.org/docs/html/gcode/g-code.html#gcode:g0

        """
        x = int(-x) if self.invert_x else int(x)
        y = int(-y) if self.invert_y else int(y)
        z = int(-z) if self.invert_z else int(z)
        self.send_cmd(f"g0 x{x} y{y} z{z}")
        self.x, self.y, self.z = x, y, z
        time.sleep(0.1)  # Add a little sleep between calls
        return None

    def wait(self):
        """ Send a 1-second wait (dwell) command to Grbl.

        References
        ----------
        http://linuxcnc.org/docs/html/gcode/g-code.html#gcode:g4

        """
        self.send_cmd("g4 p1")
        return None

    def send_cmd(self, cmd):
        """ Send given command to Grbl.

        Parameters
        ----------
        cmd : str
            A Grbl compatible command.

        References
        ----------
        https://github.com/gnea/grbl/wiki/Grbl-v1.1-Commands

        """
        self.serial_port.reset_input_buffer()
        logger.debug(f"{cmd} -> cnc")
        self.serial_port.write((cmd + "\n").encode())
        grbl_out = self.serial_port.readline()
        logger.debug(f"cnc -> {grbl_out.strip()}")
        time.sleep(0.1)
        return grbl_out

    def get_status(self) -> dict:
        """ Returns Grbl status."""
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
            pos = [-float(p) for p in pos]  # why - ?
            res_fmt['position'] = pos
        except:
            return None
        return res_fmt

    def get_grbl_settings(self) -> dict:
        """ Returns the Grbl settings as a dictionary {'param': value}."""
        self.serial_port.reset_input_buffer()
        self.serial_port.write(("$$" + "\n").encode())
        str_settings = self.serial_port.readlines()
        settings = {}
        for line in str_settings:
            line = line.strip()  # remove potential leading and trailing whitespace & eol
            line = line.decode()
            if not line.startswith('$'):
                # All params are prefixed with a dollar sign '$'
                continue
            param, value = line.split("=")
            try:
                settings[param] = int(value)
            except ValueError:
                settings[param] = float(value)

        logger.info("Grbl settings loaded from firmware!")
        return settings

    def print_grbl_settings(self):
        """ Print the Grbl settings.

        See Also
        --------
        GRBL_SETTINGS

        References
        ----------
        https://github.com/gnea/grbl/wiki/Grbl-v1.1-Configuration#grbl-settings

        """
        settings = self.get_grbl_settings()
        print("Obtained Grbl settings:")
        for param, value in settings.items():
            param_name, param_unit = GRBL_SETTINGS[param]
            if param_unit in ['boolean', 'mask']:
                param_unit = f"({param_unit})"
            print(f" - ({param}) {param_name}: {value} {param_unit}")
        return None

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

"""A collection of various utilities.

"""
import sys

from serial.tools import list_ports

from plantimager.log import logger


def guess_port(info):
    """Guess the USB port using a given information.

    Parameters
    ----------
    info : str
        The information to use to search ports.

    Notes
    -----
    Search for ports using a regular expression. Port ``name``, ``description`` and ``hwid`` are searched (case insensitive).
    The function returns an iterable that contains the same data that comports() generates, but includes only those entries that match the regexp.

    See Also
    --------
    serial.tools.list_ports.grep

    Examples
    --------
    >>> from plantimager.utils import guess_port
    >>> guess_port("A")  # This should yield a "More than one serial device" error...
    >>> guess_port("007")  # This should yield a "No serial device" error...
    >>> guess_port("Arduino")  # This should return the port of the CNC (if using the X-Carve as the controller is based on an Arduino UNO)

    """
    device = [p for p in list(list_ports.grep(info))]
    if len(device) > 1:
        logger.warning(f"More than one serial device has been found with '{info}'!")
        [logger.warning(f"  * {dev.device} - {dev.description} - {dev.hwid}") for dev in device]
        sys.exit("Non unique serial device ID!")
    elif len(device) == 0:
        logger.warning(f"No serial device has been found with '{info}'!")
        sys.exit("No serial device found!")
    else:
        device = device[0]

    return device.device

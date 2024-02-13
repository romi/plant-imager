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

import time
from typing import List

from plantimager.hal import AbstractScanner
from plantimager.path import Pose


class Scanner(AbstractScanner):
    """The Scanner class to combine control of CNC, Gimbal & Camera.

    Attributes
    ----------
    cnc : plantimager.hal.AbstractCNC
        A class dedicated to CNC control.
    gimbal: plantimager.hal.AbstractGimbal
        A class dedicated to Gimbal control.
    camera : plantimager.hal.AbstractCamera
        A class dedicated to Camera control.
    waiting_time: float, optional
        The time, in seconds, to wait for stabilization after setting position, default is 1.

    See Also
    --------
    plantimager.hal.AbstractScanner

    Example
    -------
    >>> from plantimager.scanner import Scanner
    >>> # Example #1 - A dummy scanner
    >>> from plantimager.dummy import CNC
    >>> from plantimager.dummy import Gimbal
    >>> from plantimager.dummy import Camera
    >>> cnc = CNC()
    >>> gimbal = Gimbal()
    >>> camera = Camera()
    >>> dummy_scanner = Scanner(cnc, gimbal, camera)
    >>> # Example #2 - A scanner with CNC & Gimbal connected via USB and an URL Camera
    >>> from plantimager.grbl import CNC
    >>> from plantimager.blgimbal import Gimbal
    >>> from plantimager.urlcam import Camera
    >>> cnc = CNC("/dev/ttyACM0", x_lims=[0, 800], y_lims=[0, 800], z_lims=[0, 100])
    >>> gimbal = Gimbal("/dev/ttyACM1", has_tilt=False, invert_rotation=True)
    >>> camera = Camera("http://192.168.0.1:8080")
    >>> scanner = Scanner(cnc, gimbal, camera)

    """

    def __init__(self, cnc, gimbal, camera, waiting_time=1.):
        """Scanner constructor.

        Parameters
        ----------
        cnc : plantimager.hal.AbstractCNC
            A class dedicated to CNC control.
        gimbal: plantimager.hal.AbstractGimbal
            A class dedicated to Gimbal control.
        camera : plantimager.hal.AbstractCamera
            A class dedicated to Camera control.
        waiting_time: float, optional
            The time, in seconds, to wait for stabilization after setting position, default is 1.
        """
        super().__init__()
        self.cnc = cnc
        self.gimbal = gimbal
        self.camera = camera
        self.waiting_time = waiting_time  # time to wait for stabilization after setting position

    def get_position(self) -> Pose:
        """Get the current position of the scanner as a 5D Pose."""
        x, y, z = self.cnc.get_position()
        pan, tilt = self.gimbal.get_position()
        return Pose(x, y, z, pan, tilt)

    def set_position(self, pose: Pose) -> None:
        """Set the position of the scanner from a 5D Pose.

        The _stabilization waiting time_ is done at the end of this step.
        """
        if self.cnc.async_enabled():
            self.cnc.moveto_async(pose.x, pose.y, pose.z)
            self.gimbal.moveto_async(pose.pan, pose.tilt)
            self.cnc.wait()
            self.gimbal.wait()
        else:
            self.cnc.moveto(pose.x, pose.y, pose.z)
            self.gimbal.moveto(pose.pan, pose.tilt)
        time.sleep(self.waiting_time)
        return

    def grab(self, idx, metadata=None):
        """Grab data with an id and metadata.

        Parameters
        ----------
        idx : int
            Id of the data `DataItem` to create.
        metadata : dict, optional
            Dictionary of metadata associated to the camera data.

        Returns
        -------
        plantimager.hal.DataItem
            The image data.

        See Also
        --------
        plantimager.hal.AbstractCamera
        plantimager.hal.AbstractScanner
        """
        return self.camera.grab(idx, metadata)

    def channels(self):
        """Channel names associated to grabbed data with the grab method.

        Returns
        -------
        List of str
            The list of channel names.

        See Also
        --------
        plantimager.hal.AbstractCamera
        """
        return self.camera.channels()

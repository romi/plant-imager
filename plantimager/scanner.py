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

from plantimager.hal import AbstractCNC
from plantimager.hal import AbstractCamera
from plantimager.hal import AbstractGimbal
from plantimager.hal import AbstractScanner
from plantimager.path import Pose


class Scanner(AbstractScanner):
    """The Scanner class to combine control of CNC, Gimbal & Camera.

    Attributes
    ----------
    cnc : AbstractCNC
        A class dedicated to CNC control.
    gimbal: AbstractGimbal
        A class dedicated to Gimbal control.
    camera : AbstractCamera
        A class dedicated to Camera control.
    waiting_time: float, optional
        The time, in seconds, to wait for stabilization after setting position, default is 1.

    """

    def __init__(self, cnc, gimbal, camera1, camera2, waiting_time=1.):
        """Scanner constructor.

        Parameters
        ----------
        cnc : AbstractCNC
            A class dedicated to CNC control.
        gimbal: AbstractGimbal
            A class dedicated to Gimbal control.
        camera : AbstractCamera
            A class dedicated to Camera control.
        waiting_time: float, optional
            The time, in seconds, to wait for stabilization after setting position, default is 1.
        """
        super().__init__()
        self.cnc = cnc
        self.gimbal = gimbal
        self.camera1 = camera1
        self.camera2 = camera2
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

    def grab(self, idx: int, metadata: dict = None):
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
        return self.camera1.grab(idx, metadata), self.camera2.grab(idx, metadata)

    def channels(self) -> List[str]:
        """Channel names associated to grabbed data with the grab method.

        Returns
        -------
        List[str]
            The image data.

        See Also
        --------
        plantimager.hal.AbstractCamera
        """
        return self.camera1.channels(), self.camera2.channels()

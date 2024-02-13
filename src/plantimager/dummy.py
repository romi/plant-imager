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

"""The dummy module offers CNC, Gimbal & Camera implementation

"""

import imageio
import numpy as np

from plantimager.hal import AbstractCNC
from plantimager.hal import AbstractCamera
from plantimager.hal import AbstractGimbal
from plantimager.hal import DataItem
from plantimager.units import deg


class CNC(AbstractCNC):
    """A dummy CNC for testing purposes.

    TODO: enable workspace origin offset, motor seed configuration,...

    Attributes
    ----------
    position : list
        The current `pan` and `tilt` positions of the gimbal.
    x_lims : (int, int), optional
        The allowed range of X-axis positions.
    y_lims : (int, int), optional
        The allowed range of Y-axis positions.
    z_lims : (int, int), optional
        The allowed range of Z-axis positions.

    Example
    -------
    >>> from plantimager.dummy import CNC
    >>> cnc = CNC()
    >>> cnc.get_position()
    [80.5, 80.79, 15.46]
    >>> cnc.home()
    >>> cnc.get_position()
    [0.0, 0.0, 0.0]
    >>> cnc.moveto(20, 20, 5)
    >>> cnc.get_position()
    [20.0, 20.0, 5.0]

    """

    def __init__(self, homing=False, x_lims=[0., 100.], y_lims=[0., 100.], z_lims=[0., 30.]):
        """
        Parameters
        ----------
        homing : bool, optional
            If ``True``, axes homing will be performed upon CNC object instantiation.
        x_lims : (float, float), optional
            The allowed range of X-axis positions. Defaults to ``[0., 100.]``
        y_lims : (float, float), optional
            The allowed range of Y-axis positions. Defaults to ``[0., 100.]``
        z_lims : (float, float), optional
            The allowed range of Z-axis positions. Defaults to ``[0., 30.]``

        Notes
        -----
        If `homing` is false, a random initial position will be generated.
        """
        super().__init__()
        self.x_lims = x_lims
        self.y_lims = y_lims
        self.z_lims = z_lims
        self.position = self._random_position()
        self.start(homing)

    def _random_position(self):
        rng = np.random.default_rng(5)
        return [round(rng.uniform(*ax, size=1)[0], 2) for ax in [self.x_lims, self.y_lims, self.z_lims]]

    def start(self, homing=False):
        """Start the CNC.

        Parameters
        ----------
        homing : bool
            If ``True``, performs homing procedure.
        """
        if homing:
            self.home()
        else:
            pass

    def stop(self):
        pass

    def home(self):
        """Performs axes homing procedure, setting axes position to their origin."""
        self.position = [0., 0., 0.]

    def get_position(self) -> list:
        """Returns the XYZ position of the CNC."""
        return self.position

    def async_enabled(self):
        return True

    def moveto(self, x: float, y: float, z: float):
        """Move axes to target XYZ position.

        Parameters
        ----------
        x, y, z : float
            The target XYZ position, in millimeters.
        """
        self.position[0] = float(x)
        self.position[1] = float(y)
        self.position[2] = float(z)
        self.wait()

    def moveto_async(self, x: float, y: float, z: float):
        """Move axes to target XYZ position.

        Parameters
        ----------
        x, y, z : float
            The target XYZ position, in millimeters.
        """
        self.position[0] = float(x)
        self.position[1] = float(y)
        self.position[2] = float(z)

    def wait(self):
        pass


class Gimbal(AbstractGimbal):
    """A dummy Gimbal for testing purposes.

    Attributes
    ----------
    position : list
        The current `pan` and `tilt` positions of the gimbal.
    pan_lims : (float, float), optional
        The allowed range of pan-axis positions. Defaults to ``[0., 360.]``
    tilt_lims : (float, float), optional
        The allowed range of tilt-axis positions. Defaults to ``[-90., 90.]``

    Example
    -------
    >>> from plantimager.dummy import Gimbal
    >>> gimbal = Gimbal()
    >>> gimbal.get_position()
    [289.8, 55.43]
    >>> gimbal.moveto(90, 10)
    >>> gimbal.get_position()
    [90.0, 10.0]
    >>> gimbal.home()
    >>> gimbal.get_position()
    [0.0, 0.0]

    """

    def __init__(self, homing=False, pan_lims=[0., 360.], tilt_lims=[-90., 90.]):
        """
        Parameters
        ----------
        homing : bool, optional
            If ``True``, axes homing will be performed upon CNC object instantiation.
        pan_lims : (float, float), optional
            The allowed range of pan-axis positions. Defaults to ``[0., 360.]``
        tilt_lims : (float, float), optional
            The allowed range of tilt-axis positions. Defaults to ``[-90., 90.]``

        Notes
        -----
        If `homing` is false, a random initial position will be generated.
        """
        super().__init__()
        self.pan_lims = pan_lims
        self.tilt_lims = tilt_lims
        self.position = self._random_position()
        self.start(homing)

    def _random_position(self):
        rng = np.random.default_rng(5)
        return [round(rng.uniform(*ax, size=1)[0], 2) for ax in [self.pan_lims, self.tilt_lims]]

    def start(self, homing=False):
        """Start the Gimbal.

        Parameters
        ----------
        homing : bool
            If ``True``, performs homing procedure.
        """
        if homing:
            self.home()
        else:
            pass
        return

    def stop(self):
        """Stop the Gimbal."""
        pass

    def home(self):
        """Performs axes homing procedure, setting axes position to their origin."""
        self.position = [0., 0.]
        return

    def has_position_control(self) -> bool:
        return False

    def get_position(self) -> list:
        """Returns the pan & tilt position of the Gimbal."""
        return self.position

    def moveto(self, pan: deg, tilt: deg):
        """Move the pan & tilt axes to given position."""
        self.position[0] = float(pan)
        self.position[1] = float(tilt)
        self.wait()

    def async_enabled(self) -> bool:
        return True

    def moveto_async(self, pan: deg, tilt: deg):
        """Move the pan & tilt axes to given position."""
        self.position[0] = float(pan)
        self.position[1] = float(tilt)
        return

    def wait(self):
        pass


class Camera(AbstractCamera):
    def __init__(self, path: str = None):
        self.path = path
        if path is not None:
            self.image = imageio.imread(self.path)
        else:
            self.image = np.rand(10, 10, 3)

    def channels(self):
        return ["rgb"]

    def grab(self, idx: int, metadata: dict = None):
        data_item = DataItem(idx, metadata)
        data_item.add_channel("rgb", self.image)
        return data_item

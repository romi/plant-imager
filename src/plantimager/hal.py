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

from abc import ABC
from abc import ABCMeta
from abc import abstractmethod
from typing import List
from typing import Tuple

import numpy as np
from plantimager.log import configure_logger
from plantimager.path import Pose
from plantimager.units import deg
from plantimager.units import length_mm
from tqdm import tqdm

from plantdb import io

logger = configure_logger(__name__)


class ChannelData(object):
    def __init__(self, name: str, data: np.array, idx: int):
        self.data = data
        self.idx = idx
        self.name = name

    def format_id(self):
        return "%05d_%s" % (self.idx, self.name)


class DataItem(object):
    def __init__(self, idx: int, metadata=None):
        self.channels = {}
        self.metadata = metadata
        self.idx = idx

    def add_channel(self, channel_name: str, data: np.array) -> None:
        self.channels[channel_name] = ChannelData(channel_name, data, self.idx)

    def channel(self, channel_name: str) -> ChannelData:
        return self.channels[channel_name]


class AbstractCNC(metaclass=ABCMeta):
    """Abstract CNC class."""

    def __init__(self):
        pass

    @abstractmethod
    def home(self) -> None:
        pass

    @abstractmethod
    def get_position(self) -> Tuple[length_mm, length_mm, length_mm]:
        pass

    @abstractmethod
    def moveto(self, x: length_mm, y: length_mm, z: length_mm) -> None:
        pass

    @abstractmethod
    def async_enabled(self):
        pass

    @abstractmethod
    def moveto_async(self, x: length_mm, y: length_mm, z: length_mm) -> None:
        pass

    @abstractmethod
    def wait(self) -> None:
        pass


class AbstractGimbal(ABC):
    """Abstract Gimbal class."""

    @abstractmethod
    def has_position_control(self) -> bool:
        pass

    @abstractmethod
    def get_position(self) -> Tuple[deg, deg]:
        pass

    @abstractmethod
    def moveto(self, pan: deg, tilt: deg) -> None:
        pass

    @abstractmethod
    def async_enabled(self) -> bool:
        pass

    @abstractmethod
    def moveto_async(self, pan: deg, tilt: deg) -> None:
        pass

    @abstractmethod
    def wait(self) -> None:
        pass


class AbstractCamera(ABC):
    """Abstract Camera class."""

    @abstractmethod
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
        """
        pass

    @abstractmethod
    def channels(self):
        pass


class AbstractScanner(metaclass=ABCMeta):
    """An abstract scanner class.

    Attributes
    ----------
    scan_count : int
        Incremental counter saving last picture index for the ``grab`` method.
        Modified by the ``inc_count`` method.
    ext : str
        Extension to use to write image data from the ``grab`` method.
    """

    def __init__(self):
        self.scan_count = 0
        self.ext = 'jpg'
        super().__init__()

    @abstractmethod
    def get_position(self) -> Pose:
        """Get the current position of the scanner."""
        pass

    @abstractmethod
    def set_position(self, pose: Pose) -> None:
        """Set the position of the scanner from a 5D Pose."""
        pass

    @abstractmethod
    def grab(self, idx, metadata):
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
            The image data & metadata.

        See Also
        --------
        plantimager.hal.AbstractCamera
        """
        pass

    @abstractmethod
    def channels(self) -> List[str]:
        """Channel names associated to data from `grab` method.

        See Also
        --------
        plantimager.hal.AbstractCamera
        """
        pass

    def inc_count(self) -> int:
        """Incremental counter used to return a picture index for the ``grab`` method."""
        x = self.scan_count
        self.scan_count += 1
        return x

    def get_target_pose(self, elt):
        """Get the target pose from a given path element (singleton).

        Parameters
        ----------
        elt : plantimager.path.PathElement
            The path element to reach.

        Returns
        -------
        plantimager.path.Pose
            The target pose to reach.

        Notes
        -----
        If a ``Pose`` attribute is missing from the given path element, we use the value from the previous pose.
        """
        pos = self.get_position()
        target_pose = Pose()
        for attr in pos.attributes():
            if getattr(elt, attr) is None:
                setattr(target_pose, attr, getattr(pos, attr))
            else:
                setattr(target_pose, attr, getattr(elt, attr))
        return target_pose

    def scan(self, path, fileset):
        """Performs a scan, that is a series of movements and image acquisitions.

        Parameters
        ----------
        path : plantimager.path.Path
            The path to follows to acquire image.
        fileset : plantdb.FSDB.Fileset
            The output fileset used to save the image.
        """
        for x in tqdm(path, unit='pose'):
            pose = self.get_target_pose(x)
            data_item = self.scan_at(pose, x.exact_pose)
            for c in self.channels():
                f = fileset.create_file(data_item.channels[c].format_id())
                data = data_item.channels[c].data
                if "float" in data.dtype.name:
                    data = np.array(data * 255).astype("uint8")
                io.write_image(f, data, ext=self.ext)
                if data_item.metadata is not None:
                    f.set_metadata(data_item.metadata)
                f.set_metadata("shot_id", "%06i" % data_item.idx)
                f.set_metadata("channel", c)
        return

    def scan_at(self, pose, exact_pose=True, metadata=None):
        """Move to a given position and take a picture.

        Parameters
        ----------
        pose : plantimager.path.Pose
            The position of the camera to take the picture.
        exact_pose : bool, optional
            If ``True`` (default), save the given `pose` under a "pose" entry in metadata.
            Else, save it as an "approximate_pose" entry in metadata.
        metadata : dict, optional
            The dictionary of metadata to associate to this picture.

        Returns
        -------
        plantimager.hal.DataItem
            The picture data & metadata.
        """
        logger.debug(f"scanning at: {pose}")
        if metadata is None:
            metadata = {}
        if exact_pose:
            metadata = {**metadata, "pose": [pose.x, pose.y, pose.z, pose.pan, pose.tilt]}
        else:
            metadata = {**metadata, "approximate_pose": [pose.x, pose.y, pose.z, pose.pan, pose.tilt]}
        logger.debug(f"with metadata: {metadata}")
        self.set_position(pose)
        return self.grab(self.inc_count(), metadata=metadata)

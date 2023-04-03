# !/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# plantimager - Python tools for the ROMI 3D Scanner
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

import atexit
import json
import os
import socket
import subprocess
import tempfile
import time
from io import BytesIO

import imageio
import numpy as np
import psutil
import requests
from plantdb import io
from plantdb.db import File

from plantimager import path
from plantimager.hal import AbstractScanner
from plantimager.hal import DataItem
from plantimager.log import logger


def check_port(port):
    """Test if it is possible to listen to this port for TCP/IPv4 or TCP/IPv6 connections.

    Parameters
    ----------
    port : str
        The localhost port to test.

    Returns
    -------
    bool
        ``True`` if it's possible to listen on this port, ``False`` otherwise.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('127.0.0.1', port))
        sock.listen(5)
        sock.close()
        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        sock.bind(('::1', port))
        sock.listen(5)
        sock.close()
    except socket.error as e:
        return False
    return True


class VirtualScannerRunner():
    """Run a Flask server in Blender to act as the virtual scanner.

    Attributes
    ----------
    subprocess : subprocess.Popen
        The subprocess instance, initialized by the ``start`` method.
    scene : str
        Path to a Blender scene file to load.
    port : int
        The port to use to instantiate and communicate with the Flask server in Blender.

    Notes
    -----
    It initializes the flask server and then listens to HTTP requests on that port.
    The process is started with the ``start()`` method and stopped with the ``stop()`` method.
    """

    def __init__(self, scene=None, port=9001):
        """Instantiate a ``VirtualScannerRunner``.

        Parameters
        ----------
        scene : str, optional
            Path to a Blender scene file to load.
            Defaults to ``None``.
        port : int, optional
            The port to use to instantiate and communicate with the Flask server in Blender.
            Defaults to ``9001``.
        """
        self.subprocess = None
        self.scene = scene
        self.port = port

    def start(self):
        port = 9001
        self.port = port
        logger.critical('came here')
        proclist = ["romi_virtualplantimager", "--", "--port", str(self.port)]
        if self.scene is not None:
            logger.debug("scene = %s" % self.scene)
            proclist.extend(['--scene', self.scene])
        self.process = subprocess.Popen(proclist)
        atexit.register(VirtualScannerRunner.stop, self)
        while True:
            try:
                x = requests.get("http://localhost:%i" % self.port)
                break
            except:
                logger.debug("Virtual scanner not ready yet...")
                time.sleep(1)
                continue
        return

    def stop(self):
        print("killing blender...")
        parent_pid = self.process.pid
        parent = psutil.Process(parent_pid)
        for child in parent.children(recursive=True):  # or parent.children() for recursive=False
            child.kill()
        parent.kill()
        while True:
            if self.process.poll() != None:
                break
            time.sleep(1)


class VirtualScanner(AbstractScanner):
    """A virtual scanner sending HTTP requests to a host rendering the 3D virtual plant and taking pictures.

    Attributes
    ----------
    runner : plantimager.vscan.VirtualScannerRunner
        The runner for the virtual scanner process.
        It must accept POST & GET HTTP requests.
    host : str
        The virtual scanner host ip.
    port : int
        The virtual scanner host port.
    classes : list of str
        The list of classes to render.
    flash : bool
        If ``True``, light the scene with a flash.
    ext : str
        Extension to use to write image data from the ``grab`` method.
    position : plantimager.path.Pose
        The current position of the camera.
    add_leaf_displacement : bool
        If ``True``, add a random displacement to the leaf class objects after loading the virtual plant.
    """

    def __init__(self, width, height, focal, flash=False, host=None, port=5000, scene=None,
                 add_leaf_displacement=False, classes=None):
        """Instantiate a ``VirtualScanner``.
        
        Parameters
        ----------
        width : int
            The with of the image to acquire.
        height : int
            The height of the image to acquire.
        focal : int
            The focal distance to the object to acquire.
        flash : bool, optional
            If ``True``, light the scene with a flash.
            Defaults to ``False``.
        host : str, optional
            The virtual scanner host ip.
            By default, instantiate a local ``VirtualScannerRunner`` process.
        port : int, optional
            The virtual scanner host port, useful only if ``host`` is set.
            Defaults to ``5000``.
        scene : str, optional
            The scene to initialize in the  ``VirtualScannerRunner``, useful only if ``host`` is NOT set.
        add_leaf_displacement : bool, optional
            If ``True``, add a random displacement to the leaf class objects after loading the virtual plant.
            Defaults to ``False``.
        classes : list of str, optional
            The list of classes to generate pictures for.
            Defaults to ``None``.
        """
        super().__init__()

        if host == None:
            self.runner = VirtualScannerRunner(scene=scene)
            self.runner.start()
            self.host = "localhost"
            self.port = self.runner.port
        else:
            self.runner = None
            self.host = host
            self.port = port

        self.path = []
        self.classes = classes

        self.flash = flash
        self.set_intrinsics(width, height, focal)
        self.id = 0
        self.ext = "png"
        self.position = path.Pose()
        self.add_leaf_displacement = add_leaf_displacement
        logger.warning(self.add_leaf_displacement)

    def get_position(self) -> path.Pose:
        """Returns the current position of the camera."""
        return self.position

    def set_position(self, pose: path.Pose) -> None:
        """Set the new position of the camera."""
        data = {
            "rx": 90 - pose.tilt,
            "rz": pose.pan,
            "tx": pose.x,
            "ty": pose.y,
            "tz": pose.z
        }
        self.request_post("camera_pose", data)
        self.position = pose

    def set_intrinsics(self, width: int, height: int, focal: float) -> None:
        """Set the intrinsic parameters of the camera for the virtual scanner.

        Parameters
        ----------
        width : int
            The with of the image to acquire.
        height : int
            The height of the image to acquire.
        focal : int
            The focal distance to the object to acquire.
        """
        self.width = width
        self.height = height
        self.focal = focal
        data = {
            "width": width,
            "height": height,
            "focal": focal,
        }
        self.request_post("camera_intrinsics", data)

    def list_objects(self):
        """List the available objects."""
        return self.request_get_dict("objects")

    def list_backgrounds(self):
        """List the available backgrounds."""
        return self.request_get_dict("backgrounds")

    def load_object(self, file, mtl=None, palette=None, colorize=True):
        """Loads an object from a OBJ file and a palette image.

        Parameters
        ----------
        file : plantdb.FSDB.File
            The file instance corresponding to the OBJ file.
        mtl : plantdb.FSDB.File, optional
            The file instance corresponding to the MTL file.
        palette : plantdb.FSDB.File, optional
            The file instance corresponding to the palette file.
        colorize : bool, optional
            Wheter the object should be colorized in Blender.

        Returns
        -------
        requests.Response
            The response from the Blender server after uploading the files.
        """
        if type(file) == str:
            file = io.dbfile_from_local_file(file)
        if type(mtl) == str:
            mtl = io.dbfile_from_local_file(mtl)
        if type(palette) == str:
            palette = io.dbfile_from_local_file(palette)

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, file.filename)
            io.to_file(file, file_path)
            files = {"file": open(file_path, "rb")}
            if mtl is not None:
                mtl_file_path = os.path.join(tmpdir, mtl.filename)
                io.to_file(mtl, mtl_file_path)
                files["mtl"] = open(mtl_file_path, "rb")
            if palette is not None:
                palette_file_path = os.path.join(tmpdir, palette.filename)
                io.to_file(palette, palette_file_path)
                files["palette"] = open(palette_file_path, "rb")
            res = self.request_post("upload_object", {"colorize": colorize}, files)
        if self.add_leaf_displacement:
            self.request_get_dict("add_random_displacement/leaf")
        return res

    def load_background(self, file: File):
        """Loads a background from a HDRI file.

        Parameters
        ----------
        file : plantdb.FSDB.File
            The file instance corresponding to the HDRI file.

        Returns
        -------
        requests.Response
            The response from the Blender server after uploading the files.
        """
        logger.debug("loading background : %s" % file.filename)
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, file.filename)
            io.to_file(file, file_path)
            files = {"file": open(file_path, "rb")}
            return self.request_post("upload_background", {}, files)

    def request_get_bytes(self, endpoint: str) -> bytes:
        x = requests.get("http://%s:%s/%s" % (self.host, self.port, endpoint))
        if x.status_code != 200:
            raise Exception("Unable to connect to virtual scanner (code %i)" % x.status_code)
        return x.content

    def request_get_dict(self, endpoint: str) -> dict:
        b = self.request_get_bytes(endpoint)
        return json.loads(b.decode())

    def request_post(self, endpoint: str, data: dict, files: dict = None) -> requests.Response:
        x = requests.post("http://%s:%s/%s" % (self.host, self.port, endpoint), data=data, files=files)
        if x.status_code != 200:
            raise Exception("Virtual scanner returned an error (error code %i)" % x.status_code)
        return x

    def channels(self) -> list:
        """List the channels to acquire.
        
        Notes
        -----
        Default to the 'rgb' channel.
        If classes are defined, they will be returned in addition to the default and the 'background'.
        """
        if self.classes is None:
            return ['rgb']
        else:
            return ['rgb'] + self.classes + ['background']

    def get_bounding_box(self):
        """Returns the bounding-box coordinates from the Blender server."""
        return self.request_get_dict("bounding_box")

    def grab(self, idx: int, metadata: dict = None) -> DataItem:
        """Grab a picture using the virtual scanner.

        Parameters
        ----------
        idx : int
            The id of the picture.
        metadata : dict, optional
            The dictionary of metadata to associate to this picture.

        Returns
        -------
        plantimager.hal.DataItem
            The picture data & metadata.
        """
        data_item = DataItem(idx, metadata)
        for c in self.channels():
            if c != 'background':
                data_item.add_channel(c, self.render(channel=c))
            else:
                x = np.zeros(data_item.channel(self.classes[0]).data.shape)
                for c in self.classes:
                    x = np.maximum(x, data_item.channel(c).data)
                x = 1.0 - x
                data_item.add_channel("background", x)

        rt = self.request_get_dict("camera_pose")
        k = self.request_get_dict("camera_intrinsics")

        if metadata is None:
            metadata = {}

        metadata["camera"] = {
            "camera_model": k,
            **rt
        }
        return data_item

    def render(self, channel='rgb'):
        """Use the Blender server to render an image of the virtual plant.

        Parameters
        ----------
        channel : str, optional
            The name of the channel to render.
            If not 'rgb' grab a picture of a specific part of the virtual plant.
            Defaults to 'rgb', grab a picture of the whole virtual plant.

        Returns
        -------
        numpy.array
            The image array.
        """
        if channel == 'rgb':
            ep = "render"
            if self.flash:
                ep = ep + "?flash=1"
            x = self.request_get_bytes(ep)
            data = imageio.imread(BytesIO(x))
            return data
        else:
            x = self.request_get_bytes("render_class/%s" % channel)
            data = imageio.imread(BytesIO(x))
            data = data[:, :, 3]
            return data

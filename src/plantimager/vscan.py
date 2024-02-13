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
import sys
import tempfile
import time
from io import BytesIO

import imageio.v3 as iio
import numpy as np
import psutil
import requests

from plantdb.db import File
from plantdb.utils import fsdb_file_from_local_file
from plantdb.utils import to_file
from plantimager import path
from plantimager.hal import AbstractScanner
from plantimager.hal import DataItem
from plantimager.log import logger

PY_BLENDER = ["blender", "-E", "CYCLES", "-b", "-P"]


def available_port(port):
    """Test if it is possible to listen to this port for TCP/IPv4 connections.

    Parameters
    ----------
    port : int
        The localhost port to test.

    Returns
    -------
    bool
        ``True`` if it's possible to listen on this port, ``False`` otherwise.

    Examples
    --------
    >>> from plantimager.vscan import available_port
    >>> available_port(9001)
    True

    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('127.0.0.1', port))
        sock.listen(5)
        sock.close()
    except socket.error as e:
        return False
    return True


def find_available_port(port_range):
    """Find an available port.

    Parameters
    ----------
    port_range : list of int
        A len-2 list of integers specifying the range of ports to test for availability.

    Returns
    -------
    int
        The available port.

    Examples
    --------
    >>> from plantimager.vscan import find_available_port
    >>> find_available_port([9001, 9999])

    """
    port_range = range(*port_range)
    rng = np.random.default_rng(5)
    for port in rng.choice(port_range, size=len(port_range)):
        if available_port(port):
            break

    return port


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
        self.port = self._select_port(port)

    def _select_port(self, port):
        if not available_port(port):
            logger.warning(f"Specified port {port} is not available!")
            logger.info("Searching for an available port in the range '[9001, 9999]'...")
            port = find_available_port(port_range=[9001, 9999])
            try:
                assert available_port(port)
            except AssertionError:
                sys.exit(f"Could not find an available port!")
            else:
                logger.info(f"Found available port '{port}'.")
        return port

    def start(self):
        """Start the Flask server in Blender."""
        logger.info('Starting the Flask server in Blender...')
        # Initialize the list of subprocess arguments:
        proclist = ["romi_virtualplantimager.py", "--", "--port", str(self.port)]
        # Add the scene file path to the list of subprocess arguments:
        if self.scene is not None:
            logger.debug("scene = %s" % self.scene)
            proclist.extend(['--scene', self.scene])
        # Execute the subprocess as a child process:
        self.subprocess = subprocess.Popen(proclist)
        # Register the stop method to be executed upon normal subprocess termination
        atexit.register(VirtualScannerRunner.stop, self)
        # Wait for the Flask server to be ready...
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
        """Stop the Flask server in Blender."""
        logger.warning('Stopping the Flask server in Blender...')
        # Get the 'Flask server' subprocess PID:
        parent_pid = self.subprocess.pid
        parent = psutil.Process(parent_pid)
        # Recursively send SIGKILL signal to kill all children processes:
        for child in parent.children(recursive=True):  # or parent.children() for recursive=False
            child.kill()
        # Send SIGKILL signal to kill 'Flask server' subprocess:
        parent.kill()
        # Check the subprocess has been killed:
        while True:
            # If the subprocess has been killed this will return something...
            if self.subprocess.poll() is not None:
                # See: https://docs.python.org/3/library/subprocess.html#subprocess.Popen.poll
                break
            time.sleep(1)
        return


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
        The list of classes to render, must be found in the loaded OBJ.
    flash : bool
        If ``True``, light the scene with a flash.
    ext : str
        Extension to use to write image data from the ``grab`` method.
    position : plantimager.path.Pose
        The current position of the camera.
    add_leaf_displacement : bool
        If ``True``, add a random displacement to the leaf class objects after loading the virtual plant.
    """

    def __init__(self, width, height, focal, flash=False, host=None, port=9001, scene=None,
                 add_leaf_displacement=False, classes=None):
        """Instantiate a ``VirtualScanner``.
        
        Parameters
        ----------
        width : int
            The width of the image to acquire.
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
            The virtual scanner host port.
            Used only if ``host`` is NOT set.
            Defaults to ``5000``.
        scene : str, optional
            Path to the scene file to create in the  ``VirtualScannerRunner``.
            Used only if ``host`` is NOT set.
        add_leaf_displacement : bool, optional
            If ``True``, add a random displacement to the leaf class objects after loading the virtual plant.
            Defaults to ``False``.
        classes : list of str, optional
            The list of classes to generate pictures for, must be found in the loaded OBJ.
            Defaults to ``None``.
        """
        super().__init__()

        if host is None:
            self.runner = VirtualScannerRunner(scene=scene, port=port)
            self.runner.start()
            self.host = "localhost"
            self.port = self.runner.port
        else:
            self.runner = None
            self.host = host
            self.port = port

        self.classes = classes
        self.flash = flash
        self.set_intrinsics(width, height, focal)
        self.ext = "png"
        self.position = path.Pose()
        self.add_leaf_displacement = add_leaf_displacement
        if self.add_leaf_displacement:
            logger.warning("Random leaf displacement has been requested!")

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
        return

    def set_intrinsics(self, width: int, height: int, focal: float) -> None:
        """Set the intrinsic parameters of the camera for the virtual scanner.

        Parameters
        ----------
        width : int
            The width of the image to acquire.
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
        return

    def list_objects(self):
        """List the available objects."""
        return self.request_get_dict("objects")

    def list_backgrounds(self):
        """List the available backgrounds."""
        return self.request_get_dict("backgrounds")

    def load_object(self, file, mtl=None, palette=None, colorize=True):
        """Upload the OBJ, MTL and palette files to the Blender Flask server with the POST method.

        Parameters
        ----------
        file : plantdb.FSDB.File
            The `File` instance corresponding to the OBJ file.
        mtl : plantdb.FSDB.File, optional
            The `File` instance corresponding to the MTL file.
        palette : plantdb.FSDB.File, optional
            The `File` instance corresponding to the PNG palette file.
        colorize : bool, optional
            Whether the object should be colorized in Blender.

        Returns
        -------
        requests.Response
            The response from Blender Flask server after uploading the files.

        See Also
        --------
        romi_virtualplantimager.upload_object_post

        Notes
        -----
        To avoid messing up the OBJ, MTL & PNG palette files, we create a temporary copy.

        The POST method of the Blender Flask server expect:
          - a 'file' argument with the `BufferedReader` for the OBJ file [REQUIRED].
          - a 'mtl' argument with the `BufferedReader` for the MTL file [OPTIONAL].
          - a 'palette' argument with the `BufferedReader` for the PNG palette file [OPTIONAL].
          - a 'colorize' argument as boolean [OPTIONAL].
        """
        # Convert path (str) to `plantdb.FSDB.File` type if necessary (create a temporary FSDB):
        if isinstance(file, str):
            file = fsdb_file_from_local_file(file)
        if isinstance(mtl, str):
            mtl = fsdb_file_from_local_file(mtl)
        if isinstance(palette, str):
            palette = fsdb_file_from_local_file(palette)

        files = {}  # dict of `BufferedReader` to use for upload
        with tempfile.TemporaryDirectory() as tmpdir:
            # Copy the OBJ file to a temporary directory & get the `BufferedReader` from it:
            obj_file_path = os.path.join(tmpdir, file.filename)
            to_file(file, obj_file_path)
            files["obj"] = open(obj_file_path, "rb")
            # Copy the MTL file to a temporary directory & get the `BufferedReader` from it, if requested:
            if mtl is not None:
                mtl_file_path = os.path.join(tmpdir, mtl.filename)
                to_file(mtl, mtl_file_path)
                files["mtl"] = open(mtl_file_path, "rb")
            # Copy the PNG palette file to a temporary directory & get the `BufferedReader` from it, if requested:
            if palette is not None:
                palette_file_path = os.path.join(tmpdir, palette.filename)
                to_file(palette, palette_file_path)
                files["palette"] = open(palette_file_path, "rb")
            # Upload these files to the Blender Flask server:
            res = self.request_post("upload_object", {"colorize": colorize}, files)

        # Apply random leaf displacement, if requested:
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
            The response from Blender Flask server to background file upload.

        See Also
        --------
        romi_virtualplantimager.upload_background_post
        """
        logger.debug("loading background : %s" % file.filename)
        with tempfile.TemporaryDirectory() as tmpdir:
            # Copy the PNG palette file to a temporary directory & get the `BufferedReader` from it, if requested:
            file_path = os.path.join(tmpdir, file.filename)
            to_file(file, file_path)
            files = {"hdr": open(file_path, "rb")}
            res = self.request_post("upload_background", {}, files)
        return res

    def request_get_bytes(self, endpoint: str) -> bytes:
        x = requests.get("http://%s:%s/%s" % (self.host, self.port, endpoint))
        if x.status_code != 200:
            raise Exception(f"Unable to connect to virtual scanner (error code {x.status_code})!")
        return x.content

    def request_get_dict(self, endpoint: str) -> dict:
        b = self.request_get_bytes(endpoint)
        return json.loads(b.decode())

    def request_post(self, endpoint: str, data: dict, files: dict = None) -> requests.Response:
        x = requests.post("http://%s:%s/%s" % (self.host, self.port, endpoint), data=data, files=files)
        if x.status_code != 200:
            logger.critical(x.text)
            raise Exception(f"Virtual scanner returned an error code {x.status_code}!")
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

        if 'background' in self.channels():
            # Generate the background:
            bg_mask = np.zeros_like(data_item.channel(self.classes[0]).data, dtype=np.uint8)
            for c in self.classes:
                mask = data_item.channel(c).data
                bg_mask = np.maximum(bg_mask, mask)
            bg_mask = 255 - bg_mask
            data_item.add_channel("background", bg_mask)

        if metadata is None:
            metadata = {}

        metadata["camera"] = {
            "camera_model": self.request_get_dict("camera_intrinsics"),
            **self.request_get_dict("camera_pose")
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
        numpy.ndarray
            The image array.
        """
        if channel == 'rgb':
            ep = "render"
            if self.flash:
                ep = ep + "?flash=1"
            x = self.request_get_bytes(ep)
            data = iio.imread(BytesIO(x))
            return data
        else:
            x = self.request_get_bytes("render_class/%s" % channel)
            data = iio.imread(BytesIO(x))
            data = np.array(255 * (data[:, :, 3] > 10), dtype=np.uint8)
            return data

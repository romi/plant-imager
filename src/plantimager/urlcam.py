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

# import urllib
# import cv2

import imageio
from plantimager.hal import AbstractCamera
from plantimager.hal import DataItem


class Camera(AbstractCamera):
    """Camera module fetching an image serve at given URL.

    Notes
    -----
    Image should be served as `$url/scan.jpg`.

    See Also
    --------
    plantimager.hal.AbstractCamera

    Examples
    --------
    >>> from plantimager.urlcam import Camera
    >>> url = "http://192.168.0.1:8080"
    >>> cam = Camera(url)
    >>> img = cam.grab("img_001")
    >>> arr = img.channel("rgb").data
    >>> arr.shape
    >>> image = Image.fromarray(arr)
    >>> image.show()

    """

    def __init__(self, url):
        """
        Parameters
        ----------
        url : str
            URL of the camera.
        """
        self.url = url

    def channels(self):
        return ["rgb"]

    def grab(self, idx: int, metadata: dict = None):
        """Grab a picture from the camera.

        Parameters
        ----------
        idx : int
            Id of the image `DataItem` to create.
        metadata : dict, optional
            Dictionary of metadata associated to the picture.

        Returns
        -------
        plantimager.hal.DataItem
            The image data.

        Examples
        --------
        >>> from plantimager.urlcam import Camera
        >>> url = "http://192.168.0.1:8080"
        >>> cam = Camera(url)
        >>> img = cam.grab("img_001")
        >>> arr = img.channel("rgb").data

        >>> from PIL import Image
        >>> image = Image.fromarray(arr)
        >>> image.show()

        """
        data_item = DataItem(idx, metadata)
        # https://docs.python.org/3/library/http.server.html#http.server.BaseHTTPRequestHandler.wfile
        # wfile:
        #   Contains the output stream for writing a response back to the client.
        #   Proper adherence to the HTTP protocol must be used when writing to this stream in order to achieve successful interoperation with HTTP clients.
        #   Changed in version 3.6: This is an io.BufferedIOBase stream.
        # data = imageio.imread(BytesIO(requests.get(self.url+"scan.jpg").content))
        # _ = requests.get(self.url + "/scan.jpg")  # update the picture
        data = imageio.imread(self.url + "/scan.jpg")  # download it
        data_item.add_channel(self.channels()[0], data)
        return data_item

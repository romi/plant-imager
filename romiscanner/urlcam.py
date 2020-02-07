"""

    romiscanner - Python tools for the ROMI 3D Scanner

    Copyright (C) 2018 Sony Computer Science Laboratories
    Authors: D. Colliaux, T. Wintz, P. Hanappe
  
    This file is part of romiscanner.

    romiscanner is free software: you can redistribute it
    and/or modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation, either
    version 3 of the License, or (at your option) any later version.

    romiscanner is distributed in the hope that it will be
    useful, but WITHOUT ANY WARRANTY; without even the implied
    warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with romiscanner.  If not, see
    <https://www.gnu.org/licenses/>.

"""    
#import urllib
import urllib.request
import cv2
from romiscanner import hal, error
import numpy as np

from . import hal
from .hal import DataItem

class Camera(hal.AbstractCamera):
    def __init__(self, url):
        self.url = url

    def channels(self):
        return ["rgb"]

    def grab(self, idx: int, metadata: dict=None):
        data_item = hal.DataItem(idx, metadata)
        data = imageio.imread(BytesIO(requests.get(self.url).content))
        data_item.add_channel("rgb", data)
        return data_item




"""

    lettucethink-python - Python tools for the LettuceThink robot

    Copyright (C) 2018 Sony Computer Science Laboratories
    Authors: D. Colliaux, T. Wintz, P. Hanappe
  
    This file is part of lettucethink-python.

    lettucethink-python is free software: you can redistribute it
    and/or modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation, either
    version 3 of the License, or (at your option) any later version.

    lettucethink-python is distributed in the hope that it will be
    useful, but WITHOUT ANY WARRANTY; without even the implied
    warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with lettucethink-python.  If not, see
    <https://www.gnu.org/licenses/>.

"""    
import pyrealsense2 as rs
import numpy as np
from lettucethink import hal, error

class Camera(hal.Camera):
    def __init__(self, color_width=1920, color_height=1080, depth_width=1280, depth_height=720):
        self.color_width=color_width
        self.color_height=color_height
        self.depth_width=depth_width
        self.depth_height=depth_height
        self.start()
        
    def __del__(self):
        self.stop()

    def start(self):
       config = rs.config()
       config.enable_stream(rs.stream.depth, self.depth_width, self.depth_height, rs.format.z16, 30)
       config.enable_stream(rs.stream.color, self.color_width, self.color_height, rs.format.bgr8, 30)
 
       self.pipeline=rs.pipeline()
       self.pipeline.start(config)

    def stop(self):
       self.pipeline.stop()

    def get_views(self):
        return ["rgb","depth"]

    def grab(self, view="rgb"):
       if view=="rgb": 
          frameset = self.pipeline.wait_for_frames()
          frame = frameset.get_color_frame()
       if view=="depth":
          frameset = self.pipeline.wait_for_frames()
          frame = frameset.get_depth_frame()
       return np.asanyarray(frame.get_data())



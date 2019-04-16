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
import cv2
from lettucethink import hal, error

class Camera(hal.Camera):
    def __init__(self, id, width, height):
        self.requestedWidth = width
        self.requestedHeight = height
        self.id = id
        self.width = 0
        self.height = 0
        self.video = None
        self.start()
        
    def __del__(self):
        self.stop()

    def start(self):
        self.video = cv2.VideoCapture(self.id)
        if not self.video.isOpened():
            raise error.Error("Failed to open the camera with id %d" % self.id)
        self.video.set(3, self.requestedWidth)
        self.video.set(4, self.requestedHeight)
        self.width = self.video.get(3)
        self.height = self.video.get(4)

    def stop(self):
        if self.video: self.video.release()
        self.video = None

    def get_resolution(self):
        return self.width, self.height
    
    def get_channels(self):
        return ["rgb"]

    def grab(self, view=0):
        check, frame = self.video.read()
        if check:
            return frame
        else:
            raise error.Error("Failed to grab an image")




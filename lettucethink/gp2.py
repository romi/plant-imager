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
import gphoto2 as gp
import os
import imageio
from lettucethink import hal, error


class Camera(hal.Camera):
    """
    Gphoto2 Camera object.
    """

    def __init__(self):
        self.camera = None
        self.start()

    def start(self):
        self.camera = gp.Camera()
        self.camera.init()
        cfg = self.camera.get_config()
        cmode = cfg.get_child_by_name("capturemode")
        cmode.set_value(cmode.get_choice(0))  # should put in single shot mode
        self.is_started = True

    def stop(self):
        self.camera.exit()
        self.camera = None

    def get_channels(self):
        return {'rgb': 'jpg'}

    # TODO: is there a way to avoid writing the file to disk?
    def grab(self, view=None, metadata=None):
        self.grab_write("/tmp/frame.jpg")
        data_item = {
            'id': id,
            'filename': filename,
            'data': {'rgb': None},
            'metadata': metadata
        }
        data = imageio.imread("/tmp/frame.jpg")
        data_item['data']['rgb'] = data
        self.data.append(data_item)
        return data_item

    def grab_write(self, target):
        file_path = self.camera.capture(0)
        camera_file = self.camera.file_get(file_path.folder, file_path.name,
                                           gp.GP_FILE_TYPE_NORMAL)
        gp.check_result(gp.gp_file_save(camera_file, target))
        return target

    def get_data(self):
        return self.data

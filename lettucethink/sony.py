"""

    lettucethink-python - Python tools the LettuceThink robot

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
import os
import imageio
import requests
import json
from io import BytesIO
from lettucethink import hal, error

class Camera(hal.Camera):
    '''
    Sony Remote Control API.
    ''' 

    def __init__(self, api_url):
        self.available_data = {"rgb"}
        self.api_url = api_url + "/sony/camera"
        self.start()

    def __api_start_rec_mode(self):
        request_result = requests.post(self.api_url,
                          data=json.dumps({"method": "startRecMode",
                          "params": [], "id":1, "version":"1.0"}), timeout=2)
        return json.loads(request_result.content)

    def __api_take_picture(self):
        while True: #wait for availability
            request_result = requests.post(self.api_url,
                              data=json.dumps({"method": "actTakePicture",
                              "params": [], "id":1, "version":"1.0"}))
            print(request_result.content)
            result = json.loads(request_result.content)
            if 'result' in result:
                break
        url = result['result'][0][0]
        img = imageio.imread(BytesIO(requests.get(url).content))
        return img
        
        
    def start(self):
        self.__api_start_rec_mode()

        
    def stop(self):
        pass

        
    def get_views(self):
        return ["rgb"]


    def grab(self, view=None):
        return self.__api_take_picture()

    
    def grab_write(self, target):
        img = self.grab()
        imageio.imwrite(target, img)
        return target

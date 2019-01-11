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
import os
import imageio
import requests
import time
import json
import subprocess
from io import BytesIO
from lettucethink import hal, error

CAMERA_FUNCTION_SHOOT = 'Remote Shooting'
CAMERA_FUNCTION_TRANSFER = 'Contents Transfer'

class SonyCamError(Exception):
    def __init__(self, message):
        self.message = message

class SonyCamAPI(object):
    def __init__(self, device_ip, api_port, timeout=2):
        self.device_ip = device_ip
        self.api_port = api_port
        self.api_url = 'http://' + device_ip + ':' + api_port + '/sony/'
        self.timeout = timeout
        method_types = self.get_method_types()
        self.supported_methods = [x[0] for x in method_types]

    def api_call(self, endpoint, method, params=[], version='1.0'):
        request_result = requests.post(self.api_url + endpoint,
              data=json.dumps({
                  'method': method,
                  'params': params,
                  'id':1,
                  'version': version
              }),
              timeout=self.timeout)
        res = json.loads(request_result.content)
        if 'error' in res:
            err = res['error']
            raise SonyCamError('''
            Failed camera request.
            Exception code: %d
            Description: %s
            '''%(err[0], err[1]))
        if 'result' in res:
            return res['result']
        if 'results' in res:
            return res['results']
        return {}

    def start_rec_mode(self):
        return self.api_call("camera", "startRecMode")

    def take_picture(self):
        while True:
            status = self.get_camera_status()
            if status == 'ContentsTransfer':
                raise SonyCamError('Camera is in content transfer mode, cannot take picture')
            elif status == 'IDLE':
                break
            else:
                time.sleep(0.1)
                
        return self.api_call("camera", "actTakePicture")[0]

    def get_available_camera_function(self):
        return self.api_call("camera", "getAvailableCameraFunction")[0]

    def get_camera_function(self):
        return self.api_call("camera", "getCameraFunction")[0]

    def set_camera_function(self, function):
        return self.api_call("camera", "setCameraFunction", [function])[0]

    def get_storage_information(self):
        return self.api_call("camera", "getStorageInformation")[0]

    def get_source_list(self):
        return self.api_call("avContent", "getSourceList", [{"scheme" : "storage"}])[0]

    def get_content_list(self, count, uri, stIdx=0, view="flat", sort="descending"):
        return self.api_call("avContent", "getContentList", [{
            "uri" : uri,
            "stIdx" : stIdx,
            "cnt" : count,
            "view" : view,
            "sort" : sort}], version="1.3")[0]

    def get_camera_status(self):
        events = self.get_event()
        for x in events:
            if 'cameraStatus' in x:
                return x['cameraStatus']
        raise SonyCamError('Could not get camera status')

    def get_available_api_list(self):
        return self.api_call("camera", "getAvailableApiList")[0]

    def get_method_types(self, version="1.0"):
        return self.api_call("camera", "getMethodTypes", [version])

    def get_event(self, long_polling=False, version="1.0"):
        return self.api_call("camera", "getEvent", [long_polling], version=version)

    def start_shoot_mode(self):
        if ('setCameraFunction' in self.supported_methods and
            'getCameraFunction' in self.supported_methods):
            camera_function = self.get_camera_function()
            if camera_function != CAMERA_FUNCTION_SHOOT:
                self.set_camera_function(CAMERA_FUNCTION_SHOOT)
        if 'startRecMode' in self.supported_methods:
            self.start_rec_mode()
        while not self.get_camera_status() == 'IDLE':
            continue

    def start_transfer_mode(self):
        if ('setCameraFunction' in self.supported_methods and
            'getCameraFunction' in self.supported_methods):
            camera_function = self.get_camera_function()
            if camera_function != CAMERA_FUNCTION_TRANSFER:
                self.set_camera_function(CAMERA_FUNCTION_TRANSFER)
        while not self.get_camera_status() == 'ContentsTransfer':
            continue

    def adb_transfer_pictures(self, count=1):
        """
        Transfer the latest count pictures from the camera
        ADB shell must be enabled on the camera
        """
        subprocess.run(['adb', 'connect', self.device_ip])
        x = subprocess.run(['adb', 'shell', 'ls /sdcard/DCIM/100MSDCF'], capture_output=True)
        files = x.stdout.split()
        files = list(map(lambda x: x.decode(), files))
        files.sort()
        files = files[-count:]
        images = []
        for f in files:
            subprocess.run(['adb', 'pull', '/sdcard/DCIM/100MSDCF/' + f, '/tmp/'])
            im = imageio.imread('/tmp/' + f)
            images.append(im)
            print(f)
        return images


class Camera(hal.Camera):
    '''
    Sony Remote Control API.
    ''' 

    def __init__(self, device_ip,
                api_port,
                timeout=10,
                postview=False,
                use_adb=False):
        self.sony_cam = SonyCamAPI(device_ip, api_port, timeout=timeout)
        self.postview = postview
        self.use_adb = use_adb
        self.data = []
        self.start()
          
    def start(self):
        self.sony_cam.start_shoot_mode()
        
    def stop(self):
        pass
        
    def get_channels(self):
        return {'rgb' : 'jpg'}

    def grab(self, view=None, metadata=None):
        if view is not None and view != 'rgb':
            raise ValueError('Unavailable view: %s'%view)
        res = self.sony_cam.take_picture()
        url = res[0]
        filename = url[url.rfind('/')+1:]
        if '?' in filename:
            filename = filename[:filename.rfind('?')]
        id = filename[:filename.rfind('.')]
        data_item = {
            'id' : id,
            'filename' : filename,
            'data' : {'rgb' : None },
            'metadata' : metadata
        }
        if self.postview:
            data = imageio.imread(BytesIO(requests.get(url).content))
            data_item['data']['rgb'] = data
        self.data.append(data_item)
        return data_item

    def retrieve_original_images(self):
        if not self.use_adb:
            self.sony_cam.start_transfer_mode()
            uri = self.sony_cam.get_source_list()[0]['source']
            content_list = self.sony_cam.get_content_list(count=len(self.data), uri=uri)
            for data_item in self.data:
                file_found = False
                filename = data_item['filename']
                for content in content_list:
                    content = content['content']['original'][0]
                    if content['fileName'] == filename:
                        url = content['url']
                        img = imageio.imread(BytesIO(requests.get(url).content))
                        data_item['data']['rgb'] = img
                        file_found = True
                        break
                if not file_found:
                    raise Exception('Could not find file %s on camera'%filename)

            self.sony_cam.start_shoot_mode()
        else:
            images = self.sony_cam.adb_transfer_pictures(count=len(self.data))
            for i, data_item in enumerate(self.data):
                data_item['data']['rgb'] = images[i]
        return self.data

    def get_data(self):
        if not self.postview:
            self.retrieve_original_images()
        return self.data



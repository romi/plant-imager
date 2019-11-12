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
from enum import Enum
from lettucethink import hal, error
import tempfile

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
        res = json.loads(request_result.content.decode('utf-8'))
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

    def setup_camera(self, params):
        if 'FNumber' in params:
            self.api_call('camera', 'setFNumber', [params['FNumber']])
        if 'ShutterSpeed' in params:
            self.api_call('camera', 'setShutterSpeed', [params['ShutterSpeed']])
        if 'IsoSpeedRate' in params:
            self.api_call('camera', 'setIsoSpeedRate', [params['IsoSpeedRate']])
        if 'WhiteBalance' in params:
            self.api_call('camera', 'setWhiteBalance', [params['WhiteBalance']])
        if 'FlashMode' in params:
            self.api_call('camera', 'setFlashMode', [params['FlashMode']])
        if 'FocusMode' in params:
            self.api_call('camera', 'setFocusMode', [params['FocusMode']])
        

    def start_transfer_mode(self):
        if ('setCameraFunction' in self.supported_methods and
            'getCameraFunction' in self.supported_methods):
            camera_function = self.get_camera_function()
            if camera_function != CAMERA_FUNCTION_TRANSFER:
                self.set_camera_function(CAMERA_FUNCTION_TRANSFER)
        while not self.get_camera_status() == 'ContentsTransfer':
            continue

    def get_available_shoot_mode(self):
        return self.api_call("camera", "getAvailableShootMode")[1]

    def set_shoot_mode(self, mode):
        return self.api_call("camera", "setShootMode", [mode])

    def start_movie_rec(self):
        return self.api_call("camera", "startMovieRec")

    def stop_movie_rec(self):
        return self.api_call("camera", "stopMovieRec")

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

class FlashAirAPIError(Exception):
    def __init__(self, message):
        self.message = message

class FlashAirAPI(object):
    def __init__(self, host):
        self.host = host
        self.commands_format = "http://%s/command.cgi?%s"
        self.delete_format = "http://%s/upload.cgi?DEL=%s"
        self.path_format = "http://%s%s"
        requests.get(self.path_format%(self.host, "/"))

    def format_datetime(self, date, time):
        return date+time #TODO

    def format_attribute(self, attribute):
        return attribute #TODO

    def get_file_list(self, path):
        res = requests.get(self.commands_format%(self.host, "op=100&DIR=%s"%path))
        res = res.content.split()
        #print(res)
        if res[0] != b'WLANSD_FILELIST':
            raise FlashAirAPIError("Could not retrieve file list")

        files = []
        for i in range(1, len(res)):
            directory, fname, size, attribute, date, time = res[i].decode().split(',')
            datetime = self.format_datetime(date, time)
            attribute = self.format_attribute(attribute)
            files.append({
                "directory" : directory,
                "filename" : fname,
                "size" : size,
                "attribute": attribute,
                "datetime" : datetime,
            })
        return files

    def transfer_latest_pictures(self, count=1, tmpdir=None):
        dir_list = self.get_file_list('/DCIM')
        files = []
        for x in dir_list:
            if x['filename'] != '100__TSB': #Ignore file from SD card
                files.extend(self.get_file_list('/DCIM/' + x['filename']))

        files.sort(key = lambda x: x['filename'], reverse=True) #TODO: sort by date
        images = []
        fnames = []
        for i in range(count):
            if i >= len(files):
                break
            path = '%s/%s'%(files[i]['directory'],files[i]['filename'])
            url = self.path_format%(self.host, path)
            print(url)
            new_image = imageio.imread(BytesIO(requests.get(url).content), format='jpg')
            if not(tmpdir): images.append(new_image)
            else:
                #print(files[i]['filename'])
                fname =os.path.join(tmpdir,files[i]['filename'])
                imageio.imwrite(fname, new_image)
                fnames.append(fname)
                
        if not(tmpdir):
            return images[::-1]
        else:
            return fnames

    def delete_all(self):
        files=[]
        dir_list = self.get_file_list('/DCIM')
        for x in dir_list:
            if x['filename'] != '100__TSB': #Ignore file from SD card
                files.extend(self.get_file_list('/DCIM/' + x['filename']))

        for f in files:
            requests.get(self.delete_format%(self.host,f['directory']+'/'+f['filename']))
        
class Camera(hal.Camera):
    '''
    Sony Remote Control API.
    ''' 

    def __init__(self, device_ip,
                api_port,
                timeout=10,
                postview=False,
                use_adb=False,
                use_flashair=False,
                flashair_host=None,
                camera_params=None,
                tmpdir=False,
                video_camera=False):
        super().__init__(**locals())

        self.sony_cam = SonyCamAPI(device_ip, api_port, timeout=timeout)
        self.postview = postview
        self.use_flashair = use_flashair
        self.use_adb = use_adb
        if use_flashair and use_adb:
            raise SonyCamError("Cannot use both flashair and adb for transfer")
        if use_flashair:
            if flashair_host is None:
                raise SonyCamError("Must provide flashair host IP")
            self.flashair = FlashAirAPI(flashair_host)

        self.camera_params = camera_params
        self.video_camera = video_camera
        self.tmpdir = tmpdir
        self.start()

    def start(self):
        self.sony_cam.start_shoot_mode()
        if self.video_camera:
            if "movie" in self.sony_cam.get_available_shoot_mode():
                self.sony_cam.set_shoot_mode("movie")
            else:
                raise Exception("Video recording not available.")
        else:
            self.sony_cam.set_shoot_mode("still")
        if self.camera_params is not None:
            self.sony_cam.setup_camera(self.camera_params)
        
    def stop(self):
        pass
       
    def channels(self):
        if self.video_camera:
            return ['video']
        else:
            return ['rgb']

    def grab(self, metadata=None):
        if self.video_camera:
            raise Exception("Grab not available if video mode.")
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
        self.store_queue.append(data_item)


    def start_recording(self):
        if not self.video_camera:
            raise Exception("not available in still mode")
        self.sony_cam.start_movie_rec()

    def stop_recording(self):
        if not self.video_camera:
            raise Exception("not available in still mode")
        self.sony_cam.stop_movie_rec()
        id = self.format_id(self.up_id(), 'video')
        data_item = {
            'id' : id,
            'filename' : '%s.mp4'%id,
            'data' : {
                'video' : None
                },
            'metadata' : None
        }
        self.store_queue.append(data_item)

    def store(self, fileset, last_n=inf):
        if not self.postview:
            self.__retrieve_original_images()
        super().store(self)


    def __retrieve_original_images(self):
        if self.use_adb:
            images = self.sony_cam.adb_transfer_pictures(count=len(self.store_queue))
            for i, data_item in enumerate(self.store_queue):
                data_item['data']['rgb'] = images[i]
        elif self.use_flashair:
            images = self.flashair.transfer_latest_pictures(count=len(self.store_queue))
            for i, data_item in enumerate(self.store_queue):
                data_item['data']['rgb'] = images[i]
        else:
            self.sony_cam.start_transfer_mode()
            uri = self.sony_cam.get_source_list()[0]['source']
            content_list = self.sony_cam.get_content_list(count=len(self.store_queue), uri=uri)
            for i, data_item in enumerate(self.store_queue):
                file_found = False
                filename = data_item['filename']
                content = content_list[-1-i]
                # for content in content_list:
                content = content['content']['original'][0]
                # if content['fileName'] == filename:
                url = content['url']
                if self.video_camera:
                    vid = BytesIO(requests.get(url).content)
                    data_item['data']['video'] = vid
                else:
                    img = imageio.imread(BytesIO(requests.get(url).content))
                    data_item['data']['rgb'] = img
                # file_found = True
                        # break
                # if not file_found:
                    # raise Exception('Could not find file %s on camera'%filename)

            self.sony_cam.start_shoot_mode()

import gphoto2 as gp
import os
import imageio
import requests
import json
from lettucethink import hal, error

class Camera(hal.Camera):
    '''
    Sony Remote Control API.
    ''' 

    def __init__(self, api_url):
        self.available_data = {"rgb"}
        self.api_url = api_url
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

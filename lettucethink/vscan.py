from lettucethink import hal
import requests
import json
import imageio
import numpy as np
from io import BytesIO


class VirtualScanner():
    def __init__(self, host="localhost", port="5000"):
        self.host = host
        self.port = port

    def request_get(self, endpoint):
        x = requests.get("http://%s:%s/%s"%(self.host, self.port, endpoint))
        if x.status_code != 200:
            raise Exception("Unable to connect to virtual scanner (code %i)"%x.status_code)
        # If json, return content, else return bytes
        try:
            return json.loads(x.content.decode())
        except:
            return x.content

    def request_post(self, endpoint, data):
        x = requests.post("http://%s:%s/%s"%(self.host, self.port, endpoint), data=data)
        if x.status_code != 200:
            raise Exception("Unable to connect to virtual scanner (code %i)"%x.status_code)

class CNC(hal.CNC):
    def __init__(self, host="localhost", port="5000"):
        self.virtual_scanner = VirtualScanner(host, port)

    def start(self):
        pass

    def stop(self):
        pass

    def home(self):
        pass
    def set_home(self):
        pass

    def has_position_control(self):
        return True
    
    def get_position(self):
        raise NotImplementedError
    
    def moveto(self, x, y, z):
        data = {
            "tx": x,
            "ty": y,
            "tz": z
        }
        self.virtual_scanner.request_post("camera_pose", data)
    
    def async_enabled(self):
        return False

class Gimbal(hal.Gimbal):
    def __init__(self, host="localhost", port="5000"):
        self.virtual_scanner = VirtualScanner(host, port)

    def start(self):
        pass

    def stop(self):
        pass


    def home(self):
        pass

    def has_position_control(self):
        return True
    
    def get_position(self):
        raise NotImplementedError
    
    def moveto(self, pan, tilt):
        data = {
            "rx": 90 - tilt / np.pi * 180,
            "rz": pan / np.pi * 180 - 90
        }
        self.virtual_scanner.request_post("camera_pose", data)
    
    def async_enabled(self):
        return False
    

class Camera(hal.Camera):
    def __init__(self, width, height, focal, render_ground_truth=False, load_object=None, load_background=None, host="localhost", port="5000", classes=None, flash=False):
        super().__init__()
        self.virtual_scanner = VirtualScanner(host, port)

        self.width = width
        self.height = height
        self.focal = focal
        self.render_ground_truth = render_ground_truth
        self.flash = flash

        data = {
            "width": self.width,
            "height": self.height,
            "focal": self.focal,
        }
        self.virtual_scanner.request_post("camera_intrinsics", data)
        
        self.load_object = load_object
        
        if load_object != None:
            self.displacement = self.virtual_scanner.request_get("load_object/" + load_object)
        if load_background != None:
            self.virtual_scanner.request_get("load_background/" + load_background)

        if classes is None:
            self.classes = self.virtual_scanner.request_get("classes")
        else:
            self.classes = list(classes)#classes.split(',')
            print(self.classes)
        self.bounding_box = self.virtual_scanner.request_get("bounding_box")
        

    def start(self):
        pass

    def stop(self):
        pass

    
    def grab(self, metadata=None):
        data = {}
        for c in self.channels():
            data[c] = self.__grab(c)

                
        data_item = {}
        data_item["data"] = data

        rt = self.virtual_scanner.request_get("camera_pose")
        k = self.virtual_scanner.request_get("camera_intrinsics")
        if metadata is None:
            metadata = { "camera" : {} }
        else:
            metadata["camera"] = {}

        metadata["camera"] = {
            "camera_model" : k,
            **rt
        }
        data_item["metadata"] = metadata
        data_item["id"] = self.up_id()


        self.store_queue.append(data_item)

    def channels(self):
        if self.render_ground_truth:
            return ['rgb', 'segmentation']
        else:
            return ['rgb']



    def __grab(self, channel):
        if channel == 'rgb':
            ep = "render"
            if self.flash:
                ep = ep+"?flash=1"
            x = self.virtual_scanner.request_get(ep)
            data = imageio.imread(BytesIO(x))
            return data
        elif channel == 'segmentation':

            data = {}
            for i, class_name in enumerate(self.classes):
                x = self.virtual_scanner.request_get("render_class/%s"%class_name)
                data_ = imageio.imread(BytesIO(x))
                print(class_name)
                data[class_name] = data_[:,:,3]

            return data
        else:
            raise ValueError("Wrong argument (channel): %s"%channel)

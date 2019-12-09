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
    def __init__(self, width, height, focal, render_ground_truth=False, load_object=None, load_background=None, host="localhost", port="5000"):
        super().__init__()
        self.virtual_scanner = VirtualScanner(host, port)

        self.width = width
        self.height = height
        self.focal = focal
        self.render_ground_truth = render_ground_truth

        data = {
            "width": self.width,
            "height": self.height,
            "focal": self.focal,
        }
        self.virtual_scanner.request_post("camera_intrinsics", data)
        
        self.load_object = load_object
        
        if load_object != None:
            self.virtual_scanner.request_get("load_object/" + load_object)
        if load_background != None:
            self.virtual_scanner.request_get("load_background/" + load_background)
                
        self.classes = self.virtual_scanner.request_get("classes")
        

    def start(self):
        pass

    def stop(self):
        pass

    
    def grab(self, metadata=None):
        data_item = {}
        data_item["data"] = {}

        rt = self.virtual_scanner.request_get("camera_pose")
        k = self.virtual_scanner.request_get("camera_intrinsics")
        if metadata is None:
            metadata = { "camera" : {} }
        else:
            metadata["camera"] = {}

        metadata["camera"]["K"] = k
        metadata["camera"]["rot"] = [rt[0][0:3], rt[1][0:3], rt[2][0:3]]
        metadata["camera"]["tvec"] = [rt[0][3], rt[1][3], rt[2][3]]
        data_item["metadata"] = metadata
        for c in self.channels():
            data_item["data"][c] = self.__grab(c)
        data_item["id"] = self.up_id()


        self.store_queue.append(data_item)

    def channels(self):
        if self.render_ground_truth:
            return ['rgb', 'segmentation']
        else:
            return ['rgb']



    def __grab(self, channel):
        if channel == 'rgb':
            x = self.virtual_scanner.request_get("render")
            data = imageio.imread(BytesIO(x))
            return data
        elif channel == 'segmentation':
            n_classes = len(self.classes)
            data = np.zeros((n_classes, self.height, self.width))

            for i, class_name in enumerate(self.classes):
                x = self.virtual_scanner.request_get("render_class/%s"%class_name)
                data_ = imageio.imread(BytesIO(x))
                data[i, :, :] = data_[:,:,3]
            return data
        else:
            raise ValueError("Wrong argument (channel): %s"%channel)


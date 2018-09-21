import urllib
import cv2
from lettucethink import hal, error

class Camera(hal.Camera):
    def __init__(self, url):
        self.url = url

    def start(self):
        pass

    def stop(self):
        pass
    
    def get_views(self):
        return ["rgb"]

    def grab(self, view=0):
        req = urllib.request.urlopen(self.url)
        arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
        image = cv2.imdecode(arr, -1)
        return image




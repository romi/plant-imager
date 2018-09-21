import gphoto2 as gp
import os
import imageio
from lettucethink import hal, error

class Camera(hal.Camera):
    '''
    Gphoto2 Camera object.
    ''' 

    def __init__(self):
        self.available_data = {"rgb"}
        self.camera = None
        self.start()
        
        
    def start(self):
        self.camera = gp.Camera()
        self.camera.init()
        cfg = self.camera.get_config()
        cmode = cfg.get_child_by_name("capturemode")
        cmode.set_value(cmode.get_choice(0)) # should put in single shot mode
        self.is_started = True

        
    def stop(self):
        self.camera.exit()
        self.camera = None

        
    def get_views(self):
        return ["rgb"]


    # TODO: is there a way to avoid writing the file to disk?
    def grab(self, view=None):
        self.grab_write("/tmp/frame.jpg")
        return imageio.imread("/tmp/frame.jpg")

    
    def grab_write(self, target):
        file_path = self.camera.capture(0)
        camera_file = self.camera.file_get(file_path.folder, file_path.name, gp.GP_FILE_TYPE_NORMAL)
        gp.check_result(gp.gp_file_save(camera_file, target))
        return target

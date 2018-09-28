#import tifffile
import imageio
import os

class CNC(object):
    def __init__(self):
        pass

    def start(self):
        raise NotImplmentedError

    def stop(self):
        raise NotImplmentedError
    
    def home(self):
        raise NotImplmentedError
    
    def has_position_control():
        raise NotImplmentedError
    
    def get_position(self):
        raise NotImplmentedError
    
    def moveto(self, x, y, z):
        raise NotImplmentedError
    
    def async_enabled(self):
        raise NotImplmentedError
    
    def moveto_async(self, x, y, z):
        raise NotImplmentedError
    
    def wait(self):
        raise NotImplmentedError

    def has_velocity_control():
        raise NotImplmentedError
    
    def get_velocity(self):
        raise NotImplmentedError

    def moveat(self, vx, vy, vz):
        raise NotImplmentedError

    def start_spindle(self):
        raise NotImplmentedError

    def stop_spindle(self):
        raise NotImplmentedError


TOOL_NONE = 0
TOOL_GIMBAL = 1
TOOL_ROTATINGHOE = 2

class Tool(object):
    def __init__(self, type):
        self.type = type
    
    def get_tooltype():
        self.type

        
class Gimbal(Tool):
    def __init__(self):
        Tool.__init__(TOOL_GIMBAL)
    
    def has_position_control():
        raise NotImplmentedError
    
    def get_position(self):
        raise NotImplmentedError
    
    def moveto(self, pan, tilt):
        raise NotImplmentedError

    def async_enabled(self, x, y, z):
        raise NotImplmentedError
    
    def moveto_async(self, pan, tilt):
        raise NotImplmentedError

    def wait(self):
        raise NotImplmentedError

    def has_velocity_control():
        raise NotImplmentedError
    
    def get_velocity(self):
        raise NotImplmentedError

    def moveat(self, vpan, vtilt):
        raise NotImplmentedError

    
class Camera(object):
    def __init__(self):
        pass

    def start(self):
        raise NotImplmentedError

    def stop(self):
        raise NotImplmentedError

    def grab(self, view=None):
        raise NotImplmentedError

    def get_views(self):
        raise NotImplmentedError
    
    def store_views(self, dir, filetype, suffix=None):
        files = []
        for view in self.get_views():
            if suffix:
                filename = "%s-%s.%s" % (view, suffix, filetype)
            else:
                filename = "%s.%s" % (view, filetype)
            filepath = os.path.join(dir, filename)
            image = self.grab(view)
            #if filetype == "tif":
            #    tifffile.imsave(filepath, image)
            #else:
            imageio.imwrite(filepath, image)
            files.append(filepath)
        return files


    
class GameController(object):
    def __init__(self):
        pass

    def set_callback(self, name, callback):
        raise NotImplmentedError

    def handle_events(self):
        raise NotImplmentedError



class MotorController(object):
    def __init__(self):
        pass

    def reset_encoders(self):
        raise NotImplmentedError

    def moveat(self, velocity):
        raise NotImplmentedError

    def set_wheel_velocity(self, wheel, velocity):
        ''' wheel 0 is left, wheel 1 is right '''
        raise NotImplmentedError



    

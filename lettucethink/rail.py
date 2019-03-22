import serial
import time
import imageio
from lettucethink import hal, error
import datetime
#import sys


class Rail(hal.CNC):
    def __init__(self, port = "/dev/ttyACM0", baud_rate=115200, homing=False):
        self.port = port
        self.serial_port = None
        self.baud_rate = baud_rate
        self.homing = homing
        self.scale = 100000.0 / 3.745  
        self.is_async = False
        self.x = 0
        self.target_x = 0
        self.y = 0
        self.z = 0
        self.has_started = False
        self.start()
        
    def start(self, homing=False):
        print("Opening serial port")
        self.serial_port = serial.Serial(self.port, self.baud_rate)
        self.enable()
        self.has_started = True

    def stop(self):
        if self.has_started:
            self.disable()
            self.serial_port.close()
            self.has_started=False
            
    def has_position_control():
        return True

    def async_enabled(self):
        return self.is_async

    def has_velocity_control(self):
        return False

    def home(self):
        self.__send("H")

    def set_home(self):
        self.__send("0")
        
    def update_position(self):
        r=self.__send("P")
        res=str(r).split("[")[1].split("]")[0].split(",")
        self.x = self.scale * int(res[0])
        self.target_x = self.scale * int(res[1])

    def get_position(self):
        self.update_position()
        return self.x, self.target_x
        
    def moveto(self, x, y=0, z=0, pan=0, tilt=0):
        steps = (int) (x  * self.scale)
        print("%f m = %d steps" % (x, steps));
        self.__send("m%d" % steps)
        
    def moveto_async(self, x, y, z):
        steps = (int) (x  * self.scale)
        print("%f M = %d steps" % (x, steps));
        self.__send("M%d" % steps)
        
    def enable(self):
        self.__send("E1")

    def disable(self):
        self.__send("E0")

    def get_version(self):
        self.__send("?")
        
    def __send(self, s):
        if not self.serial_port:
            raise Exception("Arduino has not been started")
        r = False
        try:
            self.serial_port.write(bytes('%s\n' % s, 'utf-8'))
            time.sleep(0.01)   
            r = self.serial_port.readline()
        finally:
            pass # dummy statement to avoid empty 'finally' clause
        print('cmd=%s: %s' % (s, r))
        return r;

    

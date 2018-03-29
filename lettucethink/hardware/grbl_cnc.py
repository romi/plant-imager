#!/usr/bin/python
import serial
import time
import numpy as np

class GrblCNC(object):
    '''
    CNC functionalities 
    TODO: enable workspace origin offset, motor seed configuration,...
    ''' 
    def __init__(self, port="/dev/ttyUSB0", baud_rate=115200, homing=False, 
                       x_lims=[0,800], y_lims=[0,800], z_lims=[0,100]):
        self.port = port
        self.baud_rate = baud_rate
        self.homing = homing

        self.x_lims=x_lims
        self.y_lims=y_lims
        self.z_lims=z_lims
        self.serial_port=None

        self.x=0
        self.y=0
        self.z=0
        
    def start(self):
        self.serial_port = serial.Serial(self.port, self.baud_rate)
        self.serial_port.write("\r\n\r\n")
        time.sleep(2)
        self.serial_port.flushInput()
        if self.homing:
            self.home()
            self.send_cmd("g90")
            self.send_cmd("g21")

    def stop(self):
        self.serial_port.close()

    def home(self):
        self.send_cmd("$H")
        #self.send_cmd("g28") #reaching workspace origin
        self.send_cmd("g92 x0 y0 z0")

    def move_to(self, x, y, z):
        self.send_cmd("g0 x%s y%s z%s"%(int(x), int(y), int(z)))
        self.send_cmd("g4 p1")
        self.x = int(x)
        self.y = int(y)
        self.z = int(z)

    def send_cmd(self, cmd):
        print(cmd)
        self.serial_port.write(cmd+"\n")
        grbl_out = self.serial_port.readline()
        print(' : ' + grbl_out.strip())
        return grbl_out

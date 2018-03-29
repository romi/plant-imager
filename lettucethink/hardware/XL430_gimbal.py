#!/usr/bin/python
import serial
import time
import numpy as np
from math import pi
import pyxl430 as xl

STEPS_PER_TURN = 4096

class XL430:
    def __init__(self, port="/dev/ttyUSB1", tilt_zero=1024, pan_zero=0, tilt_idx=2, pan_idx=1):
         self.port = port
         self.serial_port=xl.USB2Dynamixel(self.port)
         self.pan_idx = pan_idx
         self.tilt_idx = tilt_idx
         self.pan_zero=pan_zero
         self.tilt_zero=tilt_zero

    def pan_angle2steps(self,angle):
        return int((angle*STEPS_PER_TURN/2/pi)+self.pan_zero)

    def tilt_angle2steps(self,angle):
        return int((angle*STEPS_PER_TURN/2/pi)+self.tilt_zero)

    def pan_step2angle(self, steps):
        return (steps-self.pan_zero)*2*pi/STEPS_PER_TURN

    def tilt_step2angle(self, steps):
        return (steps-self.tilt_zero)*2*pi/STEPS_PER_TURN

    def start(self):    
        self.serial_port.start()
        self.pan=xl.Actuator(self.serial_port, self.pan_idx)
        self.tilt=xl.Actuator(self.serial_port, self.tilt_idx)
        self.pan.reboot()
        self.tilt.reboot()
        self.pan.set_torque_enable(1)
        self.tilt.set_torque_enable(1)
        self.move_to(0, 0)

    def move_to(self, pan, tilt):
        """
        Move to given angles (in radian)
        """
        p=self.pan_angle2steps(pan)
        t=self.tilt_angle2steps(tilt)
        self.pan.set_goal_position(p)
        self.tilt.set_goal_position(t)

    def get_pan(self):
        return self.pan_step2angle(self.pan.get_present_position())

    def get_tilt(self):
        return self.tilt_step2angle(self.tilt.get_present_position())

    def set_acc(self, acc): #TODO
        return ""

    def set_speed(self, speed): #TODO
        return ""

    def set_mode(self, mode): #TODO
        return ""

    def send_cmd(self, cmd): #TODO
        return ""

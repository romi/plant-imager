#!/usr/bin/python
import serial
import time
import numpy as np
import pyxl430 as xl

class XL430:
   def __init__(self, port="/dev/ttyUSB1", tilt_zero=-1024, pan_zero=0, tilt_idx=1, pan_idx=2, pan_lims=[-360,360],tilt_lims=[-90,90], pan_homing_offset=-1024, tilt_homing_offset=-2048, N=4096):
        self.port = port
        self.serial_port=xl.USB2Dynamixel(self.port)
        self.pan=None
        self.tilt=None
        self.pan_idx=pan_idx 
        self.tilt_idx=tilt_idx 
        self.pan_offset=pan_homing_offset
        self.tilt_offset=tilt_homing_offset
        self.n_steps=N
        self.pan_lims=pan_lims
        self.pan_zero=pan_zero
        self.tilt_lims=tilt_lims
        self.tilt_zero=tilt_zero

   def pan_angle2steps(self,angle):
      return int((angle*self.n_steps/360.)-self.pan_zero)

   def tilt_angle2steps(self,angle):
      return int(-(angle*self.n_steps/360.)-self.tilt_zero)

   def pan_step2angle(self, steps):
      return (steps+self.pan_zero)*360./self.n_steps

   def tilt_step2angle(self, steps):
      return (steps+self.tilt_zero)*360./self.n_steps

   def start(self):    
        self.serial_port.start()
        self.pan=xl.Actuator(self.serial_port, self.pan_idx)
        self.tilt=xl.Actuator(self.serial_port, self.tilt_idx)
        self.pan.set_torque_enable(0)
        self.tilt.set_torque_enable(0)
        self.tilt.set_max_position_limit(2048)
        self.pan.set_homing_offset(self.pan_offset) 
        self.tilt.set_homing_offset(self.tilt_offset) 
        self.pan.set_operating_mode(3)
        self.tilt.set_operating_mode(3)
        p0=self.pan_angle2steps(0)
        t0=self.tilt_angle2steps(0)
        self.pan.set_torque_enable(1)
        self.tilt.set_torque_enable(1)
        self.pan.set_goal_position(p0) 
        self.tilt.set_goal_position(t0)
        
   def move_to(self, pan, tilt):
       p=self.pan_angle2steps(pan)
       t=self.tilt_angle2steps(tilt)
       self.pan.set_goal_position(p)
       self.tilt.set_goal_position(t)

   def get_pan(self):
      return self.pan.get_present_position()

   def get_tilt(self):
      return self.tilt.get_present_position()

   def set_acc(self, acc):
        return ""

   def set_speed(self, speed):
        return ""

   def set_mode(self, mode):
        return ""

   def send_cmd(self, cmd):
        return ""

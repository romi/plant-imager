#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from plantimager import hal
from romi.remote_device import OquamXYTheta

import math
import time

class Gimbal (hal.AbstractGimbal):
    def __init__(self, speed, registry="10.42.0.1"):
        self.speed = speed
        self.registry = registry
        self.start()

    def start (self):
        self.romiGimbal = OquamXYTheta("cnc",self.registry)
        self.romiGimbal.power_up()

    def has_position_control(self):
    	#I don't understand the utility of this function
    	#It seem it's not used anywhere 
        return False

    def oquam_position(self):
        return self.romiGimbal.get_position()

    def get_position(self):
        position = self.oquam_position()
        pan = position.get('z')
        tilt = 0
        return math.degrees(pan), tilt

    def async_enabled(self):
        return True

    def moveto(self, pan, tilt):
        self.moveto_async(pan, tilt)
        self.wait()

    def moveto_async(self, pan, tilt):
        pos = self.oquam_position()
        #pan in deg but Oquam need rad
        print("pan in deg :", pan)
        print("pan in rad :", math.radians(pan))
        self.romiGimbal.moveto(pos.get('x'), pos.get('y'), math.radians(pan), self.speed, absolute=True)
        print("moveto_async oquamGimbal")
        time.sleep(0.1)

    def wait(self):
        time.sleep(1)
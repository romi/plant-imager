#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from plantimager import hal
from romi.remote_device import OquamXYTheta

import time

class CNC(hal.AbstractCNC):
    def __init__(self, speed, registry="10.42.0.1"):
        self.speed = speed
        self.registry = registry
        self.start()

    def start (self):
        self.romiCNC = OquamXYTheta("cnc",self.registry)
        self.romiCNC.power_up()
        self.home()
        
    def home(self):
        self.romiCNC.homing()

    def oquam_position(self):
        return self.romiCNC.get_position()

    def get_position(self):
        position = self.oquam_position()
        x = position.get('x')*1000
        y = position.get('y')*1000
        z = 0
        return x, y, z

    def async_enabled(self):
        return True

    def moveto(self, x, y, z):
        self.moveto_async(x, y, z)
        self.wait()

    def moveto_async(self, x, y, z):
        pos = self.oquam_position()
        self.romiCNC.moveto(x/1000, y/1000, pos.get('z'), self.speed, absolute=True)
        print("moveto_async oquamCNC")
        time.sleep(0.1)

    def wait(self):
        time.sleep(1)
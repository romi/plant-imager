#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from plantimager import hal
from romi.remote_device import RomiCamera

import numpy as np

class Camera(hal.AbstractCamera):
    def __init__(self, topic, registry="10.42.0.1"):
        self.topic = topic
        self.registry = registry
        self.start()

    def start(self):
        self.romi_cam = RomiCamera(self.topic, self.registry)
        print("picam start")

    def channels(self):
        return ["rgb"]

    def grab(self, idx: int, metadata: dict=None):
        data_item = hal.DataItem(idx, metadata)
        data = self.romi_cam.grab_img()
        data = np.array(data)
        data_item.add_channel(self.channels()[0], data)
        print("picam grab")
        return data_item 
#!/usr/bin/python
import serial
import time
import numpy as np

"Should be renamed Active sensor"
class RotatingUnit:
    def __init__(self, port="/dev/ttyACM0", pan=0, tilt=0, pan_lims=[-360,360],tilt_lims=[-90,90]):
        self.port = port
        self.serial_port = serial.Serial(self.port, 9600)
        time.sleep(2)
        self.serial_port.flushInput()
        self.pan=pan 
        self.pan=tilt
        self.pan_lims=pan_lims
        self.tilt_lims=tilt_lims
        self.set_acc(50)
        self.set_speed(50)
        self.set_mode(1)

    def move_to(self, pan, tilt):
        self.send_cmd("p%s;t%s"%(int(pan), int(tilt)))
        self.pan  = pan
        self.tilt = tilt

    def set_acc(self, acc):
        self.send_cmd("a%s"%(int(acc)))

    def set_speed(self, speed):
        self.send_cmd("s%s"%(int(speed)))

    def set_mode(self, mode):
        self.send_cmd("m%s"%(int(mode)))

    def send_cmd(self, cmd):
        print(cmd)
        self.serial_port.write(cmd+"\n")
        out = self.serial_port.readline()
        print(' : ' + out.strip())
        return out

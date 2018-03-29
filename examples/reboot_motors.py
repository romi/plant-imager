#!/usr/bin/env python3
import pyxl430 as xl

com=xl.USB2Dynamixel("/dev/ttyUSB1")
com.start()
tilt=xl.Actuator(com, 1)
pan=xl.Actuator(com, 2)
tilt.set_torque_enable(0)
pan.set_torque_enable(0)

tilt.reboot()
pan.reboot()




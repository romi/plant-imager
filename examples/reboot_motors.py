import pyxl430 as xl

com=xl.USB2Dynamixel("/dev/ttyUSB1")
com.start()
tilt=xl.Actuator(com, 1)
pan=xl.Actuator(com, 2)

tilt.reboot()
pan.reboot()




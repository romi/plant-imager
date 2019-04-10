"""

    lettucethink-python - Python tools for the LettuceThink robot

    Copyright (C) 2018 Sony Computer Science Laboratories
    Authors: D. Colliaux, T. Wintz, P. Hanappe
  
    This file is part of lettucethink-python.

    lettucethink-python is free software: you can redistribute it
    and/or modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation, either
    version 3 of the License, or (at your option) any later version.

    lettucethink-python is distributed in the hope that it will be
    useful, but WITHOUT ANY WARRANTY; without even the implied
    warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with lettucethink-python.  If not, see
    <https://www.gnu.org/licenses/>.

"""    

import serial
import time
import threading
import ast
from lettucethink import hal, error
        
    
class MotorController(hal.MotorController):
    def __init__(self, port="/dev/ttyUSB0", input_mode="rc", control_mode="pid"):
        self.port = port
        self.serial_port = None
        self.quit_thread = False
        # The motion_status array contains 5 values: time (ms),
        # encoder left & right (steps), speed left & right (mm/s)
        self.motion_status = [0, 0, 0, 0, 0]
        # Requested target velocity
        self.velocity = [0, 0]
        self.input_mode = input_mode
        self.control_mode = control_mode
        self.position_module = None
        self.start()

        
    def start(self):
        self.serial_port = serial.Serial(self.port, 115200)
        self.quit_thread = False
        self.thread = threading.Thread(target=self._handle_serial_input)
        self.thread.start()
        self.set_input_mode(self.input_mode)
        self.set_control_mode(self.control_mode)
        self.moveat(0)
        time.sleep(2)
        self.reset_encoders()

        
    def stop(self):
        if self.serial_port:
            self.moveat(0)
            # Wait until the reading thread exists. 
            self.quit_thread = True
            self.thread.join()
            # Close the serial port
            self.serial_port.close()
            self.serial_port = None
        
        
    def set_control_mode(self, mode):
        if mode == "direct":
            self.control_mode = mode
            self.__send("d")
        elif mode == "pid":
            self.control_mode = mode
            self.__send("p")
        else:
            raise Error("Invalid control mode: %s" %mode)


    def get_control_mode(self):
        return self.control_mode

            
    def set_input_mode(self, mode):
        if mode == "rc":
            self.input_mode = mode
            self.__send("r")
        elif mode == "serial":
            self.input_mode = mode
            self.__send("s")
        else:
            raise Error("Invalid input mode: %s" %mode)


    def get_input_mode(self):
        return self.input_mode

            
    def reset_encoders(self):
            self.__send("0")

        
    def set_position_module(self, obj):
        self.position_module = obj
                

    def moveat(self, velocity):
        self.set_velocity(velocity)

                
    def set_velocity(self, velocity):
        self.velocity[0] = velocity
        self.velocity[1] = velocity
        self.__send("M%d" % velocity)

        
    def set_wheel_velocity(self, wheel, velocity):
        if wheel == 0:
            self.velocity[0] = velocity
            self.__send("L%d" % velocity)
        else:
            self.velocity[1] = velocity
            self.__send("R%d" % velocity)

        
    def __send(self, s):
        if not self.serial_port:
            raise Error("MotorController is not connected (did you call start()?)")
        self.serial_port.write(bytes('%s\n' % s, 'utf-8'))
            

    def _handle_serial_input(self):
        while not self.quit_thread:
            # FIXME: must handle some timeout mechanism. Otherwise,
            # the thread will never exit.
            line =  self.serial_port.readline().decode("utf-8")
            opcode = line[0]
            if opcode == "m":
                self._handle_motion_event(line)
            elif opcode == "#":
                print("--------------------------------------------- %s" % line[1:].strip())
        print('read_updates: done')

        
    def _handle_motion_event(self, s):
        self.motion_status = ast.literal_eval(s[1:])
        if self.position_module:
            self.position_module.update_wheel_odometry(self.motion_status)

        

    

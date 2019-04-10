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
import json
import time
import math
import numpy as np
from lettucethink import hal, error

# cmp() is no longer defined in Python3 (silly)
def cmp(a, b):
    return (a > b) - (a < b)

class CNC(hal.CNC):

    def __init__(self, port="/dev/ttyUSB0", homing=True):
        self.port = port
        self.status = "idle"
        self.p = [0, 0, 0]
        self.v = [0, 0, 0]
        self.serial_port = None
        self.start(homing)

        
    def start(self, homing=True):
        self.serial_port = serial.Serial(self.port, 115200)
        # TODO: read '#ready' ?
        while self.serial_port.in_waiting == 0:
            time.sleep(0.1)
        r = self.serial_port.readline()
        if homing: self.home()
        self.set_zero()
        self.update_status()

    def stop(self):
        if self.serial_port:
            self.serial_port.close()
            self.serial_port = None

    def home(self):
        self.__send('h')

        
    def has_position_control():
        return True

    
    def async_enabled(self):
        return True

    
    def get_position(self):
        self.update_status()
        return self.p

    
    def has_velocity_control():
        return True

    
    def get_velocity(self):
        self.update_status()
        return self.v

    
    def set_zero(self):
        self.__send('0')

        
    def start_spindle(self, ):
        self.__send('S1')

                
    def stop_spindle(self, ):
        self.__send('S0')

        
    def get_status(self):
        self.update_status()
        return self.status

    
    def moveat(self, vx, vy, vz):
        self.__send("x%d" % vx)
        self.__send("y%d" % vy)
        self.__send("z%d" % vz)

        
    def set_target_pos(self, x, y, z):
        self.__send("X%d" % x)
        self.__send("Y%d" % y)
        self.__send("Z%d" % z)


    # Dont use, doesn't work yet
    def __wait__(self):
        self.__send("W")

    def wait(self):
        time.sleep(0.1)   
        self.update_status()
        while self.status == "moving":
            time.sleep(0.1)   
            self.update_status()

        
    def moveto(self, x, y, z):
        self.moveto_async(x, y, z)
        self.wait()
        
        
    def moveto_async(self, x, y, z):
        self.update_status()
        v = 100 # FIXME: get the max speed, as defined on the firmware
        dx = x - self.p[0]
        dy = y - self.p[1]
        dz = z - self.p[2]
        d = math.sqrt(dx*dx + dy*dy + dz*dz)
        vx = v * dx / d
        vy = v * dy / d
        vz = v * dz / d
        print("v= %f, %f, %f" % (vx, vy, vz))
        self.moveto_async_v([x, y, z], [vx, vy, vz])

               
    def moveto_async_v(self, p, v):
        self.set_target_pos(p[0], p[1], p[2])
        if np.isscalar(v):
            self.__send("M%d" % v)
        else:
            self.moveat(v[0], v[1], v[2])

                
    def moveto_async_z(self, z, vz):
        self.__send("Z%d" % z)
        self.__send("z%d" % vz)

        
            
    def update_status(self):
        s = self.__send("s")
        try:
            stat = json.loads(s.decode("utf-8"))
            self.status = stat["status"]
            self.p = stat["p"]
            self.v = stat["v"]
        except KeyError as k:
            print("Failed to parse the JSON: missing key")
        except Exception as e:
            print("Failed to parse the JSON: %s" % str(e))
            print("String was: %s" % s)
        finally:
            pass # dummy statement to avoid empty 'finally' clause
        #print('status=%s, p=%s, v=%s' % (self.status, str(self.p), str(self.v)))

        
    def __send(self, s):
        if not self.serial_port:
            raise Error("CNC has not been started")
        r = False
        try:
            self.serial_port.write(bytes('%s\n' % s, 'utf-8'))
            time.sleep(0.01)   
            r = self.serial_port.readline()
        finally:
            pass # dummy statement to avoid empty 'finally' clause
        if r == False:
            print('cmd=%s: failed' % (s))
        return r;

    
if __name__ == "__main__":
    cnc = CNCVelocityControl("/dev/ttyACM0")
    rounds = 3
    xoff = 0
    for round in range(rounds):
        cnc.moveto([xoff, -600, 0], [0, -50, 0])
        cnc.moveto([xoff - 50, -600, 0], [-20, 0, 0])
        cnc.moveto([xoff - 50, 10, 0], [0, 50, 0])
        if (round < rounds - 1):
            cnc.moveto([xoff - 100, 10, 0], [-20, 0, 0])
        xoff -= 100



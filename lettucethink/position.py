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

import math
import numpy as np
import threading
#from lettucethink import hal
        

class PositionModule(object):
    def __init__(self):
        # longitude, latitude, elevation
        self.abs_position = np.array([0.0, 0.0, 0.0], dtype=np.float64)
        # x, y, z, relative to position at start-up, in millimeter 
        self.rel_position = np.array([0.0, 0.0, 0.0], dtype=np.float64)
        # ???
        self.abs_orientation = np.array([0.0, 0.0, 0.0], dtype=np.float64)
        # pan, tilt, roll, relative to orientation at start-up
        self.rel_orientation = np.array([0.0, 0.0, 0.0], dtype=np.float64)
        # velocity, in mm/s
        self.velocity = np.array([0.0, 0.0, 0.0], dtype=np.float64)
        self.lock = threading.Lock()


    def _lock(self):
        self.lock.acquire()

    def _unlock(self):
        self.lock.release()

        
    def get_relative_position(self):
        self._lock()
        copy = np.copy(self.rel_position)
        self._unlock()
        return copy

    
    def set_relative_position(self, x, y, z):
        self._lock()
        self.rel_position[0] = x
        self.rel_position[1] = y
        self.rel_position[2] = z
        self._unlock()

    
    def get_relative_orientation(self):
        self._lock()
        copy = np.copy(self.rel_orientation)
        self._unlock()
        return copy

    
    def set_relative_orientation(self, pan, tilt, roll):
        self._lock()
        self.rel_orientation[0] = pan
        self.rel_orientation[1] = tilt
        self.rel_orientation[2] = roll
        self._unlock()

    
    def update_wheel_odometry(self, x):
        raise NotImplementedError


    
class WheelPositionModule(PositionModule):
    
    def __init__(self, wheelbase, wheelCircumference, stepsPerRevolution, encoderWheelRatio):
        PositionModule.__init__(self)
        self.wheelbase = wheelbase
        self.wheelCircumference = wheelCircumference
        self.stepsPerRevolution = stepsPerRevolution
        self.encoderWheelRatio = encoderWheelRatio
        self.leftPrevEncoderTicks = 0
        self.rightPrevEncoderTicks = 0
        self.x = 0
        self.y = 0
        self.theta = 0

        
    def update_wheel_odometry(self, v):
        now = v[0]
        leftEncoderTicks = v[1]
        rightEncoderTicks = v[2]
        leftDist = self.wheelCircumference * (leftEncoderTicks - self.leftPrevEncoderTicks) / self.stepsPerRevolution / self.encoderWheelRatio
        rightDist = self.wheelCircumference * (rightEncoderTicks - self.rightPrevEncoderTicks) / self.stepsPerRevolution / self.encoderWheelRatio

        if leftDist != 0 or rightDist != 0:
            dtheta = (rightDist - leftDist) / self.wheelbase
            dx, dy, R = 0.0, 0.0, 0.0
            if dtheta == 0.0:
                dx = rightDist
                dy = 0.0
            else:
                # R is the radius over which the rover turns. Measured
                # from the middle in between the wheels.
                R = (leftDist + rightDist) / 2.0 / dtheta
                dx = R * math.sin(dtheta)
                dy = R * (1.0 - math.cos(dtheta))

            s = math.sin(self.theta)
            c = math.cos(self.theta)
            self.x += dx * c - dy * s
            self.y += dx * s + dy * c
            self.theta += dtheta
            #print("R=%f, dtheta=%f, x=%f, y=%f, theta=%f" % (R, dtheta, self.x, self.y, 180 * self.theta / math.pi))

            self.set_relative_position(self.x, self.y, 0.0)
            self.set_relative_orientation(self.theta, 0.0, 0.0)

        self.leftPrevEncoderTicks = leftEncoderTicks
        self.rightPrevEncoderTicks = rightEncoderTicks

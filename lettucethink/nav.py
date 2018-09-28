import time
import math
import position

class NavigationModule(object):
    def __init__(self, rover, positionmodule):
        self.rover = rover
        self.position = positionmodule
        #self.position = position.WheelPositionModule(rover.wheelbase,
        #                                             rover.wheelCircumference,
        #                                             rover.stepsPerRevolution,
        #                                             rover.encoderWheelRatio)
        
        # Ask the motorcontroller to send updates of the wheel
        # positions to the position_module
        self.rover.motorcontroller.set_position_module(self.position)
        

    def turn(self, angle, stop=True):
        p = self.position.get_relative_orientation()
        theta1 = p[0] + angle
        if angle > 0:
            wheel = 1
            sign = 1
            self.rover.motorcontroller.set_wheel_velocity(0, 0)
            self.rover.motorcontroller.set_wheel_velocity(1, 220)
        else:
            wheel = 0
            sign = -1
            self.rover.motorcontroller.set_wheel_velocity(0, 220)
            self.rover.motorcontroller.set_wheel_velocity(1, 0)
            
        arrived = False
        while not arrived:
            p = self.position.get_relative_orientation()
            theta = p[0]
            d = sign * (theta1 - theta)
            print("target: %d, angle: %f, delta %f" % (theta1, theta, d))
            if d < 0:
                print("d < 0")
                arrived = True
            elif d < 0.0174533: # 1 degrees
                print("d < 1 degree")
                arrived = True
            else:
                time.sleep(0.05)

        if stop: self.stand_still()

            
    def turn_degrees(self, angle, stop=True):
        self.turn(math.pi * angle / 180.0, stop)


    def stand_still(self):
        self.rover.stand_still()

        
    def moveto(self, distance, stop=True):
        p = self.position.get_relative_position()
        x0 = p[0] 
        y0 = p[1] 
        direction = 1
        if distance < 0:
            direction = -1
            distance = -distance
        speed = 300
        
        self.rover.motorcontroller.moveat(direction * speed)
    
        arrived = False
        while not arrived:
            p = self.position.get_relative_position()
            #print(p)
            x = p[0] 
            y = p[1] 
            d = math.sqrt((x - x0) * (x - x0) + (y - y0) * (y - y0))
            print("togo: %d, travelled: %f" % (distance, d))
            if d >= distance:
                print("d > d2")
                arrived = True
            elif distance - d < 10:
                print("d < 100")
                arrived = True
            elif distance - d < 50:
                if speed != 200:
                    print("speed 200")
                    speed = 200
                    self.rover.motorcontroller.moveat(direction * speed)
                    time.sleep(0.01)
            elif distance - d < 200:
                if speed != 250:
                    print("speed 250")
                    speed = 250
                    self.rover.motorcontroller.moveat(direction * speed)
                    time.sleep(0.05)
            else:
                time.sleep(0.2)

        if stop: self.stand_still()
    

    def follow_path(self, distances_and_angles, degrees=False):
        index = 0
        while index < len(distances_and_angles):
            distance = distances_and_angles[index]
            index += 1
            self.moveto(distance, stop=False)
            
            if index < len(distances_and_angles):
                angle = distances_and_angles[index]
                index += 1
                if degrees:
                    angle = math.pi * angle / 180.0
                self.turn(angle, stop=False)
        self.stand_still()

        
    def reverse_path(self, distances_and_angles, degrees=False):
        distances_and_angles.reverse()
        l = [-x for x in distances_and_angles]
        self.follow_path(l, degrees)
        

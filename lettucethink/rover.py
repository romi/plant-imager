from lettucethink import hal

class Rover(object):
    def __init__(self, cnc, motorcontroller, tool, topcam, workspace):
        self.cnc = cnc
        self.motorcontroller = motorcontroller
        self.tool = tool
        self.topcam = topcam
        self.workspace = workspace

    def stand_still(self):
        if self.motorcontroller != None:
            self.motorcontroller.moveat(0)

            

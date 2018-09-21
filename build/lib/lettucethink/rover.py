from lettucethink import hal

class Rover(object):
    def __init__(self, cnc, nav, tool, topcam, workspace):
        self.cnc = cnc
        self.nav = nav
        self.tool = tool
        self.topcam = topcam
        self.workspace = workspace

from lettucethink import hal, log
import serial
import time

class CNC(hal.CNC):
    '''
    CNC functionalities 
    TODO: enable workspace origin offset, motor seed configuration,...
    ''' 
    def __init__(self, port="/dev/ttyUSB0", baud_rate=115200, homing=False, 
                       x_lims=[0,800], y_lims=[0,800], z_lims=[-100,0]):
        self.port = port
        self.baud_rate = baud_rate
        self.homing = homing
        self.x_lims = x_lims
        self.y_lims = y_lims
        self.z_lims = z_lims
        self.serial_port = None
        self.x = 0
        self.y = 0
        self.z = 0
        #self.has_started = False
        self.start(homing)

        
    def start(self, homing=False):
        self.serial_port = serial.Serial(self.port, self.baud_rate)
        self.has_started = True
        self.serial_port.write("\r\n\r\n".encode())
        time.sleep(2)
        self.serial_port.flushInput()
        if self.homing:
            self.home()
            self.send_cmd("g90")
            self.send_cmd("g21")

    def stop(self):
        if (self.has_started):
            self.serial_port.close()

            
    def has_position_control():
        return True

    
    def get_position(self):
        return self.x, self.y, self.z 

    
    def async_enabled(self):
        return True

    
    def has_velocity_control():
        return False

    
    def home(self):
        self.send_cmd("$H")
        #self.send_cmd("g28") #reaching workspace origin
        self.send_cmd("g92 x0 y0 z0")

                    
    def moveto(self, x, y, z):
        self.moveto_async(x, y, z)
        self.wait()

        
    def moveto_async(self, x, y, z):
        self.send_cmd("g0 x%s y%s z%s" % (int(x), int(y), int(z)))
        self.x = int(x)
        self.y = int(y)
        self.z = int(z)
        time.sleep(0.1) # Add a little sleep between calls

        
    def wait(self):
        self.send_cmd("g4 p1")

    
    def start_spindle(self):
        self.send_cmd("M3 S12000")

    
    def stop_spindle(self):
        self.send_cmd("M5")

    
    def send_cmd(self, cmd):
        log.write("cnc", cmd)
        self.serial_port.write((cmd + "\n").encode())
        grbl_out = self.serial_port.readline()
        log.write("cnc", "-> %s" % grbl_out.strip())
        return grbl_out

# Released by rdb under the Unlicense (unlicense.org)
# Based on information from:
# https://www.kernel.org/doc/Documentation/input/joystick-api.txt

import os, struct, array
import fcntl
from lettucethink import hal

# These constants were borrowed from linux/input.h
axis_names = {
    0x00 : 'x',
    0x01 : 'y',
    0x02 : 'z',
    0x03 : 'rx',
    0x04 : 'ry',
    0x05 : 'rz',
    0x06 : 'trottle',
    0x07 : 'rudder',
    0x08 : 'wheel',
    0x09 : 'gas',
    0x0a : 'brake',
    0x10 : 'hat0x',
    0x11 : 'hat0y',
    0x12 : 'hat1x',
    0x13 : 'hat1y',
    0x14 : 'hat2x',
    0x15 : 'hat2y',
    0x16 : 'hat3x',
    0x17 : 'hat3y',
    0x18 : 'pressure',
    0x19 : 'distance',
    0x1a : 'tilt_x',
    0x1b : 'tilt_y',
    0x1c : 'tool_width',
    0x20 : 'volume',
    0x28 : 'misc',
}

button_names = {
    0x120 : 'trigger',
    0x121 : 'thumb',
    0x122 : 'thumb2',
    0x123 : 'top',
    0x124 : 'top2',
    0x125 : 'pinkie',
    0x126 : 'base',
    0x127 : 'base2',
    0x128 : 'base3',
    0x129 : 'base4',
    0x12a : 'base5',
    0x12b : 'base6',
    0x12f : 'dead',
    0x130 : 'a',
    0x131 : 'b',
    0x132 : 'c',
    0x133 : 'x',
    0x134 : 'y',
    0x135 : 'z',
    0x136 : 'tl',
    0x137 : 'tr',
    0x138 : 'tl2',
    0x139 : 'tr2',
    0x13a : 'select',
    0x13b : 'start',
    0x13c : 'mode',
    0x13d : 'thumbl',
    0x13e : 'thumbr',

    0x220 : 'dpad_up',
    0x221 : 'dpad_down',
    0x222 : 'dpad_left',
    0x223 : 'dpad_right',

    # XBox 360 controller uses these codes.
    0x2c0 : 'dpad_left',
    0x2c1 : 'dpad_right',
    0x2c2 : 'dpad_up',
    0x2c3 : 'dpad_down',
}



def list_devices():
    # Iterate over the joystick devices.
    print('Available devices:')
    for fn in os.listdir('/dev/input'):
        if fn.startswith('js'):
            print('  /dev/input/%s' % (fn))


class GameController(hal.GameController):
    def __init__(self, dev = '/dev/input/js0'):
        self.axis_states = {}
        self.button_states = {}
        self.axis_map = []
        self.button_map = []
        self.callbacks = {}
        
        print('Opening %s...' % dev)
        self.jsdev = open(dev, 'rb')
        fd = self.jsdev.fileno()
        flag = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, flag | os.O_NONBLOCK)
        flag = fcntl.fcntl(fd, fcntl.F_GETFL)
        if flag & os.O_NONBLOCK:
            print("O_NONBLOCK!")
        
        self.__init_name()
        self.__init_axes()
        self.__init_buttons()        


    def __init_name(self):
        buf = array.array('b', [0] * 64)
        fcntl.ioctl(self.jsdev, 0x80006a13 + (0x10000 * len(buf)), buf) # JSIOCGNAME(len)
        self.name = buf.tostring()
        print('Device name: %s' % self.name)

        
    def __init_axes(self):
        buf = array.array('B', [0])
        fcntl.ioctl(self.jsdev, 0x80016a11, buf) # JSIOCGAXES
        self.num_axes = buf[0]
        
        buf = array.array('B', [0] * 0x40)
        fcntl.ioctl(self.jsdev, 0x80406a32, buf) # JSIOCGAXMAP
        
        for axis in buf[:self.num_axes]:
            name = axis_names.get(axis, 'unknown(0x%02x)' % axis)
            self.axis_map.append(name)
            self.axis_states[name] = 0.0
            self.callbacks[name] = False

        print('%d axes found: %s' % (self.num_axes, ', '.join(self.axis_map)))

        
    def __init_buttons(self):
        buf = array.array('B', [0])
        fcntl.ioctl(self.jsdev, 0x80016a12, buf) # JSIOCGBUTTONS
        self.num_buttons = buf[0]
        
        buf = array.array('H', [0] * 200)
        fcntl.ioctl(self.jsdev, 0x80406a34, buf) # JSIOCGBTNMAP
            
        for btn in buf[:self.num_buttons]:
            name = button_names.get(btn, 'unknown(0x%03x)' % btn)
            self.button_map.append(name)
            self.button_states[name] = 0
            self.callbacks[name] = False
            
        print('%d buttons found: %s' % (self.num_buttons, ', '.join(self.button_map)))

        
    def set_callback(self, name, callback):
        self.callbacks[name] = callback

        
    def get_axis(self, name):
        return self.axis_states[name]

    
    def handle_events(self):
        while True:
            evbuf = self.jsdev.read(8)
            if not evbuf: break
        
            time, value, type, number = struct.unpack('IhBB', evbuf)

            if type & 0x80:
                print("(initial)")

            elif type & 0x01:
                name = self.button_map[number]
                #print("button %s" % name)
                self.button_states[name] = value
                callback = self.callbacks[name]
                if callback: callback(name, value)
            
            elif type & 0x02:
                name = self.axis_map[number]
                if self.axis_states[name] != value:
                    self.axis_states[name] = value
                    callback = self.callbacks[name]
                    if callback: callback(name, value)

        
        


import serial

def cnc_init(port="/dev/ttyUSB0"):
    cnc = serial.Serial(port, 115200)
    cnc.write("\r\n\r\n")
    time.sleep(2)
    cnc.flushInput()
    cnc_homing()
    cnc_send_cmd("G90")
    cnc_send_cmd("G21")
    return cnc

def cnc_send_cmd(cmd, cnc):
    print cmd
    cnc.write(cmd + " \n")
    grbl_out = cnc.readline()
    print ' : ' + grbl_out.strip()
    return grbl_out

def cnc_moveto(newx, newy, newz, cnc):
    # tell CNC to move to new position
    cnc_send_cmd("G0 x%s y%s z%s\n"%(int(10*newx), int(10*newy), -int(10*newz)), cnc)
    # wait for reply from CNC
    cnc_send_cmd("G4 P1", cnc)
    return

def cnc_homing(cnc):
    cnc_send_cmd("$H",cnc)
    cnc_send_cmd("g28",cnc)
    cnc_send_cmd("g92 x0 y0 z0",cnc)
    # get new position
    cnc_update_position(0, 0, 0,cnc)
    return

def cnc_stop():
    return

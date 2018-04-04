#!/usr/bin/env python3
from lettucethink.robot import Robot
import lettucethink.utils as ut
import lettucethink as lt
import getopt
import sys
from sys import argv

import datetime
import time
import json
import pydepthsense as pds

scan_dir = "scan"

cnc_port = "/dev/ttyUSB0"
gimbal_port = "/dev/ttyUSB1"
homing = False

pars={"xc": 400,
      "yc": 400,
      "zc":  0,
      "r" : 350,
      "nc": 6
     }

if __name__ == '__main__':
    opts, args = getopt.getopt(argv[1:], "hHc:g:d:n:r:")
    for opt, arg in opts:
        print(opt)
        if opt == '-h':
            print('centered_scan.py [-H<homing>] -c <cnc_port=/dev/ttyUSB0> -g <gimbal_port=/dev/ttyUSB1> -d <directory=./scan/> -n <num_points=10> -r <radius=35> -z <cnc_z=0 > -t <gimbal_tilt=0>')
            sys.exit()
        if opt == '-H':
            homing = True
        elif opt == "-c":
            cnc_port = arg
        elif opt == "-g":
            gimbal_port = arg
        elif opt == "-d":
            scan_dir = arg
        elif opt == "-n":
            pars["nc"] = int(arg)
        elif opt == "-r":
            pars["r"] = int(arg)
        elif opt == "-z":
            pars["z"] = int(arg)
        elif opt == "-":
            pars["t"] = int(arg)
            
    t0=time.time()

    json.dump(pars,open(scan_dir+"pars.json","w"))
    #lscan=Robot.create_robot_grbl_gp2_xl430(scan_dir=scan_dir,homing=homing,cnc_port=cnc_port,gimbal_port=gimbal_port)
    lscan=Robot.create_robot_grbl_ds_xl430(scan_dir=scan_dir,homing=homing,cnc_port=cnc_port,gimbal_port=gimbal_port)
    try:
        lscan.start()
        lscan.t0=pars["t"]
        lscan.circular_scan(pars["xc"],pars["yc"],pars["zc"],pars["r"],pars["nc"])

        t=time.time()-t0

        print("it took", t," s")
    except Exception as e:
        print(e)
    finally:
        lscan.stop()

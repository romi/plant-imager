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


scandir = "scan/"

cnc_port = "/dev/ttyUSB0"
gimbal_port = "/dev/ttyUSB1"

pars={"xc": 40,
      "yc": 40,
      "zc":  0,
      "r" : 35,
      "nc": 6
     }

if __name__ == '__main__':
    opts, args = getopt.getopt(argv[1:], "hc:g:d:n:r:")
    for opt, arg in opts:
        print(opt)
        if opt == '-h':
            print('centered_scan.py -c <cnc_port=/dev/ttyUSB0> -g <gimbal_port=/dev/ttyUSB1> -d <directory=./scan/> -n <num_points=10> -r <radius=35>')
            sys.exit()
        elif opt == "-c":
            cnc_port = arg
        elif opt == "-g":
            gimbal_port = arg
        elif opt == "-d":
            scandir = arg
        elif opt == "-n":
            pars["nc"] = int(arg)
        elif opt == "-r":
            pars["r"] = int(arg)

    t0=time.time()

    json.dump(pars,open(scandir+"pars.json","w"))
    lscan=Robot(scandir,homing=False,cnc_port=cnc_port,gimbal_port=gimbal_port)
    #pds.start()

    lscan.circular_scan(pars["xc"],pars["yc"],pars["zc"],pars["r"],pars["nc"])

    pds.close()
    t=time.time()-t0

    print("it took", t," s")

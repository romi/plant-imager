from lettucethink.robot import Robot
import lettucethink.utils as ut
import lettucethink as lt

import datetime
import time
import json
import pydepthsense as pds

scandir = "scan/"

pars={"xc": 40,
      "yc": 40,
      "zc":  0,
      "r" : 35,
      "nc": 6
     }

t0=time.time()

json.dump(pars,open(scandir+"pars.json","w"))
lscan=Robot(scandir,homing=False)
#pds.start()

lscan.circular_scan(pars["xc"],pars["yc"],pars["zc"],pars["r"],pars["nc"])

pds.close()
t=time.time()-t0

print "it took", t," s"

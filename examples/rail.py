import lettucethink
from lettucethink.fsdb import DB
from lettucethink import scan
from lettucethink.sony import Camera
from lettucethink.rail import Rail

camera_args = {
                    "device_ip" : "192.168.100.5",
                    "api_port" : "10000",
                    "use_adb" : False,
                    "use_flashair" : True,
                    "flashair_host" : "192.168.100.6",
                    "timeout" : 10,
                    "tmpdir" : True     
                    }

rail_args = {
            "port" : "/dev/ttyACM0",
            "homing" : False
            }

path_config = {
        "id" : "linear_10",
        "type" : "linear",
        "args" : {
                    "num_points" : 2,
                    "origin"     : 0,
                    "length"     : .2,
                    "y"          : 0,
                    "z"          : 0,
                    "pan"        : 0,
                    "tilt"       : 0
                }
    }

object_metadata={
           "object"     : "ground",
           "environment": "csl workshop",
           "culture"    : "None"
     }
 
metadata = {
            "object" : object_metadata,
            "scanner" : "None",
            "path" : path_config
        }
 
scan_id="test"


db = DB("/home/pi/data")
db.connect()


print("rail start")
rail = Rail(**rail_args)

print("camera start")
camera = Camera(**camera_args)

"""
print(path_config["args"])
scanner = scan.Scanner(rail, None, camera, db, scan_id=scan_id)
scanner.do_linear_scan(**path_config["args"])
db.disconnect()
"""

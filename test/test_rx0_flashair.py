from lettucethink.sony import Camera
import requests
import json

camera_args = {
                "device_ip" : "192.168.100.5",
                "api_port" : "10000",
                "use_adb" : False,
                "use_flashair" : True,
                "flashair_host" : "192.168.100.6",
                "timeout" : 10
                }

"""
cam=Camera(**camera_args)
cam.start()
cam.grab()
im=cam.get_data()
"""

request_result = requests.post("http://192.168.100.5:10000/sony/camera",
              data=json.dumps({
                  'method': "getMethodTypes",
                  'params': [1.0],
                  'id':1,
                  'version': "1.0"
              }),
             timeout=3)

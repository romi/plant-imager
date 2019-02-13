from lettucethink.sony import Camera
<<<<<<< HEAD
import imageio
=======
import requests
import json
>>>>>>> b44984259dff93a6da61b4f85bde7787c4381a16

camera_args = {
                "device_ip" : "192.168.100.5",
                "api_port" : "10000",
                "use_adb" : False,
                "use_flashair" : True,
                "flashair_host" : "192.168.100.6",
                "timeout" : 10
<<<<<<< HEAD
              }

=======
                }

"""
>>>>>>> b44984259dff93a6da61b4f85bde7787c4381a16
cam=Camera(**camera_args)
cam.start()
cam.grab()
im=cam.get_data()
<<<<<<< HEAD
imageio.imwrite("rx0_test.jpg",im[0]["data"]["rgb"])
=======
"""

request_result = requests.post("http://192.168.100.5:10000/sony/camera",
              data=json.dumps({
                  'method': "getMethodTypes",
                  'params': [1.0],
                  'id':1,
                  'version': "1.0"
              }),
             timeout=3)
>>>>>>> b44984259dff93a6da61b4f85bde7787c4381a16

from lettucethink.sony import Camera
import imageio

camera_args = {
                "device_ip" : "192.168.100.5",
                "api_port" : "10000",
                "use_adb" : False,
                "use_flashair" : True,
                "flashair_host" : "192.168.100.6",
                "timeout" : 10
              }

cam=Camera(**camera_args)
cam.start()
cam.grab()
im=cam.get_data()
imageio.imwrite("rx0_test.jpg",im[0]["data"]["rgb"])

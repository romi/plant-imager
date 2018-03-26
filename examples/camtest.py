from lettucethink.hardware import camera

cam=camera.Camera("HD")
#cam.grab_datas("test/", 0)

#cam.setMode("HD")
cam.grab_datas("test/", 1,["HD"])
#cam.setMode("depth")
#cam.grab_datas("test/", 1)

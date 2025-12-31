from picamzero import Camera
from time import sleep
cam = Camera()
cam.start_preview()
sleep(1000)
cam.stop_preview() 
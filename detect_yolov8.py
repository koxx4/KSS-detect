import cv2
import time
from ultralytics import YOLO
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import CircularOutput

model = YOLO("yolov5nu-v7-b-q.onnx")
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(
    main={"format": 'RGB888', "size": (1920, 1080)}))

picam2.start()

fourcc = cv2.VideoWriter_fourcc(*'MJPG')
out = cv2.VideoWriter('filename.avi', fourcc, 10, (1920, 1080))

while True:
    im = picam2.capture_array()

    if not im.any():
        continue
    # rgb = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    # resized = cv2.resize(rgb, (640, 360), interpolation = cv2.INTER_AREA)
    results = model(source=im)

    out.write(results[0].plot())

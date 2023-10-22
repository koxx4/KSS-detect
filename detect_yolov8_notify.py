import socket
import signal
import sys
import json
import os
from ultralytics import YOLO
from picamera2 import Picamera2

model = YOLO("yolov5nu-v7.onnx")
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(
    main={"format": 'RGB888', "size": (1920, 1080)}))

picam2.start()

socket_path = "/tmp/kss_detect.sock"

try:
    os.unlink(socket_path)
except OSError:
    if os.path.exists(socket_path):
        raise

# Utworzenie gniazda
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

# Połącz z gniazdem
sock.bind(socket_path)
sock.listen(1)

# accept connections
print('Server is listening for incoming connections...')
connection, client_address = sock.accept()
print('Connection from', str(connection).split(", ")[0][-4:])


def cleanup():
    print("Closing socket...")
    sock.close()

    print("Closing camera...")
    picam2.stop()


def signal_handler(sig, frame):
    cleanup()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

while True:
    im = picam2.capture_array()

    if not im.any():
        continue

    results = model(source=im)

    # A dictionary of class names
    detected_classes = results[0].names
    serialized_data = json.dumps(detected_classes)
    print(serialized_data)

    try:
        connection.sendall(serialized_data.encode())
    except OSError as e:
        print(f"There is no server listening on {socket_path}")

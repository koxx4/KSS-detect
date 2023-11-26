import cv2
from bson import ObjectId
from picamera2 import Picamera2
from ultralytics import YOLO

from event import KssEvent
from event_object import EventObject

model = YOLO("yolov5nu-v7-b-q.onnx")
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(
    main={"format": 'RGB888', "size": (1920, 1080)}))
picam2.start()

fourcc = cv2.VideoWriter_fourcc(*'MJPG')
out = cv2.VideoWriter('inference.avi', fourcc, 10, (1920, 1080))

while True:
    im = picam2.capture_array()

    if not im.any():
        continue

    results = model(source=im)
    class_counts = {}

    for box, prob, class_id in zip(results.boxes, results.probs, results.names):
        class_name = results.names[class_id]
        if class_name not in class_counts:
            class_counts[class_name] = {'count': 0, 'total_confidence': 0}
        class_counts[class_name]['count'] += 1
        class_counts[class_name]['total_confidence'] += prob.mean().item()

    processed_objects = [
        EventObject(name=class_name, count=info['count'],
                    avg_confidence=info['total_confidence'] / info['count'])
        for class_name, info in class_counts.items()
    ]

    kss_event = KssEvent(objects=processed_objects, image_id=ObjectId())
    print(kss_event)  # or handle the kss_event as needed

    out.write(results[0].plot())

import logging
import cv2
from picamera2 import Picamera2
from ultralytics import YOLO
from pymongo import MongoClient
from loguru import logger

from kss_event_service import KssEventService
from event import KssEvent
from event_object import EventObject

model = YOLO("yolov5nu-v9-a-q.onnx")
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(
    main={"format": 'RGB888', "size": (1920, 1080)}))
picam2.start()

logging.basicConfig(level=logging.DEBUG)

client = MongoClient('mongodb://localhost:27017/?replicaSet=rs0')
db = client['kss']

event_service = KssEventService(
    db, input_duration_threshold=0, output_duration_threshold=0)
event_service.listen_for_config_changes()

while True:
    im = picam2.capture_array()

    if not im.any():
        continue

    results = model(im)[0]

    detected_objects = {}
    is_event_important = False

    for i, result in enumerate(results):
        cls = int(result.boxes.cls[0].item())
        confidence = float(result.boxes.conf[0].item())
        name = result.names[cls]

        if not event_service.should_object_be_considered(name, confidence * 100):
            logger.debug(f"{name} should not be considered, confidence was {confidence}")
            continue
        
        bounding_box = result.boxes.xyxy[0].cpu().numpy()

        x = int(bounding_box[0])
        y = int(bounding_box[1])
        width = int(bounding_box[2] - x)
        height = int(bounding_box[3] - y)
        bbox = [x, y, width, height]

        if event_service.is_object_important(object_name=name):
            logger.debug(f"{name} is important")
            is_event_important = True

        if name not in detected_objects:
            detected_objects[name] = {
                'count': 0, 'total_confidence': 0, 'bounding_boxes': []}

        detected_objects[name]['count'] += 1
        detected_objects[name]['total_confidence'] += confidence
        detected_objects[name]['bounding_boxes'].append(bbox)

    processed_objects = [
        EventObject(name=class_name, count=info['count'],
                    avg_confidence=info['total_confidence'] / info['count'])
        for class_name, info in detected_objects.items()
    ]

    kss_event = KssEvent(objects=processed_objects, important=is_event_important)

    _, encoded_image = cv2.imencode('.jpg', results.plot())
    image_bytes = encoded_image.tobytes()

    event_service.save_event(event=kss_event, event_image_bytes=image_bytes)

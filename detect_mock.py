import logging
import os
import random
import time

from pymongo import MongoClient

from event import KssEvent
from event_object import EventObject
from kss_event_service import KssEventService
from object_tracker import ObjectTracker

logging.basicConfig(level=logging.DEBUG)


def load_image_paths(image_folder):
    image_paths = [os.path.join(image_folder, file) for file in os.listdir(image_folder) if file.endswith('.jpg')]
    return image_paths


image_mock_folder = 'mock_images'
image_paths = load_image_paths(image_mock_folder)


def load_image_as_bytes(image_path):
    with open(image_path, 'rb') as image_file:
        return image_file.read()


def mock_object_generator(events_probabilities, max_delay=10):
    object_names = list(events_probabilities.keys())

    while True:
        detected_objects: list[EventObject] = []
        for object_name in object_names:
            if random.random() < events_probabilities[object_name]:
                detected_objects.append(EventObject(
                    name=object_name,
                    count=random.randint(1, 5),
                    avg_confidence=random.uniform(0.5, 1.0),
                ))

        if detected_objects:
            random_image_path = random.choice(image_paths)
            image_bytes = load_image_as_bytes(random_image_path)

            generated_event = KssEvent(
                objects=detected_objects,
                important=random.choice([True, False]),
            )
            yield generated_event, image_bytes

        time.sleep(random.uniform(1, max_delay))


probabilities = {
    "Fire": 0.2,
    "Smoke": 0.3,
    "Human": 0.7,
    "Other": 0.9,
    "Open pot": 0.8,
    "Open pot boiling": 0.8,
    "Closed pot": 0.6,
    "Closed pot boiling": 0.6,
    "Dish": 0.5,
    "Gas": 0.2,
    "Pan": 0.8,
    "Closed pan": 0.8,
}

client = MongoClient('localhost', 27017)
db = client['kss']

generator = mock_object_generator(probabilities, max_delay=6)
event_service = KssEventService(db, input_duration_threshold=3, output_duration_threshold=3)

for event, event_image in generator:
    if event.objects:
        event_service.save_event(event=event, event_image_bytes=event_image)

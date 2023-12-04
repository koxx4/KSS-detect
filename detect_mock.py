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
                important= True if random.randint(1, 10) == 1 else False,
            )
            yield generated_event, image_bytes

        time.sleep(random.uniform(1, max_delay))


probabilities = {
    "fire": 0.2,
    "smoke": 0.3,
    "human": 0.7,
    "other": 0.9,
    "open_pot": 0.8,
    "open_pot_boiling": 0.8,
    "closed_pot": 0.6,
    "closed_pot_boiling": 0.6,
    "dish": 0.5,
    "gas": 0.2,
    "pan": 0.8,
    "closed_pan": 0.8,
}

client = MongoClient('mongodb://localhost:27017/?replicaSet=rs0')
db = client['kss']

generator = mock_object_generator(probabilities, max_delay=6)
event_service = KssEventService(db, input_duration_threshold=3, output_duration_threshold=3)
event_service.listen_for_config_changes()

for event, event_image in generator:
    if event.objects:
        event_service.save_event(event=event, event_image_bytes=event_image)

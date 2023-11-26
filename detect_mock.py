import logging
import os
import random
import time

import gridfs
from pymongo import MongoClient

from event import KssEvent
from event_object import EventObject
from object_tracker import ObjectTracker

logging.basicConfig(level=logging.DEBUG)


def load_image_paths(image_folder):
    image_paths = [os.path.join(image_folder, file) for file in os.listdir(image_folder) if file.endswith('.jpg')]
    return image_paths


image_mock_folder = 'mock_images'
image_paths = load_image_paths(image_mock_folder)

client = MongoClient('localhost', 27017)
db = client['kss']


def load_image_as_bytes(image_path):
    with open(image_path, 'rb') as image_file:
        return image_file.read()


def save_event_to_mongo(kss_event: KssEvent, kss_event_image: bytes):
    collection = db['kss-events']

    fs = gridfs.GridFS(db)
    image_id = fs.put(kss_event_image)
    kss_event.image_id = image_id

    event_data = kss_event.__dict__()
    collection.insert_one(event_data)


def mock_object_generator(events_probabilities, max_delay=10, tracker: ObjectTracker = None):
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
            if tracker:
                tracker.update(detected_objects)
                stable_objects_ids = tracker.get_stable_objects()

                # Debug print visualizing differences between objects lists
                previous_set = {obj.name_count_id for obj in detected_objects}
                current_set = {obj_id for obj_id in stable_objects_ids}

                removed = previous_set - current_set
                print("Removed objects:", ", ".join(removed))

                # Replace detected objects with stable objects that
                # were qualified by object tracker
                detected_objects = [obj for obj in detected_objects if obj.name_count_id in stable_objects_ids]
                print(f"Finally persistent objects: {[obj.__str__() for obj in detected_objects]}")

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

generator = mock_object_generator(probabilities, max_delay=6, tracker=ObjectTracker(3.0, 3.0))

for event, event_image in generator:
    if event.objects:
        save_event_to_mongo(kss_event=event, kss_event_image=event_image)
    print(event)

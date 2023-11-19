import os
import pickle
import random
import time

import gridfs
from pymongo import MongoClient

from event import KssEvent


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


def save_event_to_mongo(kss_event: KssEvent):
    collection = db['kss-events']

    # Sprawdzenie rozmiaru obrazu
    if len(kss_event.image) > 16 * 1024 * 1024:  # większy niż 16MB
        fs = gridfs.GridFS(db)
        image_id = fs.put(kss_event.image)
        kss_event.image = image_id  # Zapisanie referencji do obrazu w GridFS
    else:
        kss_event.image = kss_event.image

    # Zapisanie reszty danych do kolekcji
    event_data = kss_event.__dict__
    collection.insert_one(event_data)


def mock_object_generator(events_probabilities, max_delay=2):
    object_names = list(events_probabilities.keys())

    while True:
        generated_objects = []
        for object_name in object_names:
            if random.random() < events_probabilities[object_name]:
                random_image_path = random.choice(image_paths)
                image_bytes = load_image_as_bytes(random_image_path)

                generated_objects.append(KssEvent(
                    name=object_name,
                    count=random.randint(1, 5),
                    image=image_bytes,
                    confidence=random.uniform(0.5, 1.0),
                    important=random.choice([True, False]),
                    bounding_boxes=[
                        [random.randint(0, 100), random.randint(0, 100), random.randint(0, 100), random.randint(0, 100)]
                        for _ in range(random.randint(1, 3))]
                ))
        yield generated_objects
        time.sleep(random.uniform(1, max_delay))


# Użycie:
# Definiowanie prawdopodobieństwa wystąpienia każdego obiektu
probabilities = {
    "Fire": 0.7,  # 70% szans na pojawienie się ognia
    "Smoke": 0.4,  # 40% szans na dym
    "Person": 0.9  # 90% szans na osobę
}

generator = mock_object_generator(probabilities)

for objects in generator:
    print(objects)
    for event in objects:
        save_event_to_mongo(kss_event=event)

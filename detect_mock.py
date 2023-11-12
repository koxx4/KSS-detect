import random
import time
import numpy as np
import gridfs
import pickle
from pymongo import MongoClient
from event import KssEvent

client = MongoClient('localhost', 27017)
db = client['kss']


def save_event_to_mongo(kss_event: KssEvent):
    collection = db['kss-events']

    # Konwersja obrazu do formatu binarnego
    image_binary = pickle.dumps(kss_event.image)

    # Sprawdzenie rozmiaru obrazu
    if len(image_binary) > 16 * 1024 * 1024:  # większy niż 16MB
        fs = gridfs.GridFS(db)
        image_id = fs.put(image_binary)
        kss_event.image = image_id  # Zapisanie referencji do obrazu w GridFS
    else:
        kss_event.image = image_binary

    # Zapisanie reszty danych do kolekcji
    event_data = kss_event.__dict__
    collection.insert_one(event_data)


def mock_object_generator(events_probabilities, max_delay=2):
    object_names = list(events_probabilities.keys())

    while True:
        generated_objects = []
        for object_name in object_names:
            if random.random() < events_probabilities[object_name]:
                generated_objects.append(KssEvent(
                    name=object_name,
                    count=random.randint(1, 5),
                    image=np.random.rand(100, 100, 3),  # Mock obrazu jako ndarray
                    confidence=random.uniform(0.5, 1.0),
                    important=random.choice([True, False]),
                    bounding_boxes=[
                        (random.randint(0, 100), random.randint(0, 100), random.randint(0, 100), random.randint(0, 100))
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

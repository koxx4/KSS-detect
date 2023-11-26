from datetime import datetime, timezone
from bson import ObjectId

from event_object import EventObject


class KssEvent:

    def __init__(self,
                 objects: list[EventObject],
                 image_id: ObjectId | None = None,
                 date=None,
                 important=False,
                 read=False):
        if objects is None:
            objects = {}
        self.objects = objects
        self.image_id = image_id
        self.date = date if date is not None else datetime.now()
        self.important = important
        self.read = read

    def __dict__(self) -> dict:
        return {
            'objects': [obj.__dict__() for obj in self.objects],
            'image_id': self.image_id,
            'date': self.date,
            'important': self.important,
            'read': self.read
        }

    def __str__(self):
        return (f"DetectedObjects(\n"
                f"  Objects: {self.objects}\n"
                f"  Image ID: {self.image_id}\n"
                f"  Date: {self.date}\n"
                f"  Important: {self.important}\n"
                f"  Read: {self.read}\n)")

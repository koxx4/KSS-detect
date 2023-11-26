from datetime import datetime

import pytz
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
            objects = []
        self.objects = objects
        self.image_id = image_id
        self.date = date if date is not None else pytz.utc.localize(datetime.utcnow())
        self.important = important
        self.read = read

    @property
    def object_ids(self) -> set[str]:
        """Zwraca zbiór identyfikatorów zdarzeń z obiektów."""
        if self.objects is None:
            return set()

        return {obj.name_count_id for obj in self.objects}

    @property
    def object_ids_str(self) -> str:
        """Zwraca zbiór identyfikatorów zdarzeń z obiektów."""
        if self.objects is None:
            return ''

        return ', '.join(self.object_ids)

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

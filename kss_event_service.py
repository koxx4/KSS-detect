import gridfs
from loguru import logger

from event import KssEvent
from event_change_detector import EventChangeDetector
from object_tracker import ObjectTracker


class KssEventService:
    def __init__(self,
                 db,
                 input_duration_threshold=0,
                 output_duration_threshold=0,
                 force_save_empty_events=False,
                 change_detector_on=True):
        self.db = db
        self.object_tracker = ObjectTracker(input_duration_threshold, output_duration_threshold)
        self.event_change_detector = EventChangeDetector()
        self.force_save_empty_events = force_save_empty_events
        self.change_detector_on = change_detector_on

    def save_event(self, event: KssEvent, event_image_bytes: bytes | None = None):
        logger.debug(f"Received an event for saving: {event.object_ids_str}")

        stable_objects = []

        if self.object_tracker.duration_thresholds_non_zero():
            self.object_tracker.update(event.objects)
            stable_objects_ids = self.object_tracker.get_stable_objects()
            stable_objects = [obj for obj in event.objects if obj.name_count_id in stable_objects_ids]
        else:
            stable_objects = event.objects

        event.objects = stable_objects

        if stable_objects or (self.force_save_empty_events and not stable_objects):

            new_event: bool = self.event_change_detector.has_changed(event)

            if new_event:
                self._save_event_to_mongo(event, event_image_bytes)
                logger.debug(f"Saved event: {event.object_ids_str}")
            else:
                logger.debug(f"New event {event.object_ids_str} was the same as previous, skipping...")

    def _save_event_to_mongo(self, event: KssEvent, event_image_bytes: bytes | None = None):
        logger.debug(f"Saving event to MongoDB: {event.object_ids_str}")

        collection = self.db['kss-events']

        if event_image_bytes:
            fs = gridfs.GridFS(self.db)
            image_id = fs.put(event_image_bytes)
            event.image_id = image_id
            logger.debug(f"Save event image: {image_id}")

        event_data = event.__dict__()
        collection.insert_one(event_data)

    def set_tracker_thresholds(self, input_duration_threshold, output_duration_threshold):
        self.object_tracker.input_duration_threshold = input_duration_threshold
        self.object_tracker.output_duration_threshold = output_duration_threshold
        logger.debug(
            f"ObjectTracker thresholds set: input={input_duration_threshold}, output={output_duration_threshold}")

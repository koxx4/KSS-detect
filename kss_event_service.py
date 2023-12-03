import threading

import gridfs
from loguru import logger
from pymongo import MongoClient

from event import KssEvent
from event_change_detector import EventChangeDetector
from kss_settings import KssSettings, KssEventConfig
from object_tracker import ObjectTracker

USER_PREFERENCES_COLLECTION = 'user-preferences'


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
        self.settings = self.init_kss_settings()

    def init_kss_settings(self) -> KssSettings | None:
        collection = self.db[USER_PREFERENCES_COLLECTION]
        settings_data = collection.find_one({"_id": 1})

        settings = None

        if settings_data:
            events_config = [KssEventConfig(event['event_name'], event['precision_threshold'], event['important']) for
                             event in settings_data['events_config']]
            settings = KssSettings(settings_data['system_on'], settings_data['input_threshold'],
                                   settings_data['output_threshold'], events_config)
            logger.info("KSS settings initialized")
        else:
            logger.warning("No settings found in the database")

        return settings

    def listen_for_config_changes(self):
        def watch_config():
            logger.debug("Starting config change stream...")
            client = MongoClient('mongodb://localhost:27017/?replicaSet=rs0')
            db = client.kss
            collection = db['user-preferences']

            with collection.watch() as stream:
                for change in stream:
                    logger.debug(f"Change detected: {change}")
                    if change['operationType'] == 'update':
                        new_config = collection.find_one({'_id': 1})
                        self.apply_new_config(new_config)

        config_thread = threading.Thread(target=watch_config)
        config_thread.start()

    def apply_new_config(self, config):
        logger.debug(f"New config detected: {config}")

        self.settings.system_on = config['system_on']
        self.settings.input_threshold = config['input_threshold']
        self.settings.output_threshold = config['output_threshold']
        self.settings.events_config = [
            KssEventConfig(event['event_name'], event['precision_threshold'], event['important']) for
            event in config['events_config']]

        self.set_tracker_thresholds(self.settings.input_threshold, self.settings.output_threshold)

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

    def is_system_on(self) -> bool:
        return self.settings.system_on

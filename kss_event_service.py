import threading

import gridfs
from loguru import logger
from pymongo import MongoClient

from event import KssEvent
from event_change_detector import EventChangeDetector
from kss_settings import KssSettings, KssEventConfig
from object_tracker import ObjectTracker
from push_utils import send_important_event_message

USER_PREFERENCES_COLLECTION = 'user-preferences'

OBJECT_TRANSLATIONS = {
    "fire": "Ogień",
    "smoke": "Dym",
    "human": "Człowiek",
    "other": "Inne",
    "open_pot": "Otwarty garnek",
    "open_pot_boiling": "Gotujący się otwarty garnek",
    "closed_pot": "Zamknięty garnek",
    "closed_pot_boiling": "Gotujący się zamknięty garnek",
    "dish": "Naczynie",
    "gas": "Gaz",
    "pan": "Patelnia",
    "closed_pan": "Zamknięta patelnia",
}

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
        self.settings = None
        self.init_kss_settings()

    def init_kss_settings(self) -> KssSettings:
        collection = self.db[USER_PREFERENCES_COLLECTION]
        settings_data = collection.find_one({"_id": 1})
        
        settings = None

        if settings_data:
            events_config = [KssEventConfig(event['event_name'], event['precision_threshold'], event['important']) for
                             event in settings_data['events_config']]
            settings = KssSettings(settings_data['system_on'], settings_data['input_threshold'],
                                   settings_data['output_threshold'], events_config)
            # FIXME
            self.set_tracker_thresholds(settings.input_threshold, settings.output_threshold)
            self.settings = settings
            self.apply_new_config(settings_data)
            logger.info("KSS settings initialized")
        else:
            logger.warning("No settings found in the database")


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

    def save_event(self, event: KssEvent, event_image_bytes: bytes = None):
        logger.debug(f"Received an event for saving: {event.object_ids_str}")

        stable_objects = []

        if self.object_tracker.duration_thresholds_non_zero():
            self.object_tracker.update(event.objects)
            stable_objects_ids = self.object_tracker.get_stable_objects()
            stable_objects = [obj for obj in event.objects if obj.name_count_id in stable_objects_ids]
        else:
            logger.debug("Skipping object tracker because tresholds where set to zero")
            stable_objects = event.objects

        event.objects = stable_objects

        if stable_objects or (self.force_save_empty_events and not stable_objects):

            new_event: bool = self.event_change_detector.has_changed(event)

            if new_event:
                self._save_event_to_mongo(event, event_image_bytes)

                if event.important:
                    push_tokens = self.get_push_tokens()
                    obj_names = [OBJECT_TRANSLATIONS.get(obj.name, obj.name) for obj in event.objects]

                    for token in push_tokens:
                        logger.info(f"Event {event.object_ids_str} was important, sending push notification!")
                        send_important_event_message(obj_names, token)

                logger.debug(f"Saved event: {event.object_ids_str}")
            else:
                logger.debug(f"New event {event.object_ids_str} was the same as previous, skipping...")

    def _save_event_to_mongo(self, event: KssEvent, event_image_bytes: bytes = None):
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

    def is_object_important(self, object_name: str) -> bool:
        return any(obj.important and obj.event_name == object_name for obj in self.settings.events_config)
    
    def should_object_be_considered(self, object_name, current_precision) -> bool:
        return any(current_precision >= obj.precision_threshold and obj.event_name == object_name for obj in self.settings.events_config)

    def get_push_tokens(self) -> list[str]:
        """Pobiera zapisane tokeny push z bazy danych."""
        collection = self.db['push-tokens']
        push_tokens = collection.find({})

        return [token_doc["token"] for token_doc in push_tokens]
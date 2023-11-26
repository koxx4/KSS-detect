import logging
import time

from event_object import EventObject


class ObjectTracker:
    """
    Tracker do śledzenia stabilności obiektów wykrytych przez określony czas.

    Atrybuty:
        input_duration_threshold (float): Minimalny czas, przez który obiekt musi być wykrywany, aby zostać uznany za stabilny.
        output_duration_threshold (float): Maksymalny czas braku wykrycia obiektu, po którym zostaje on usunięty.
        first_seen (dict): Słownik przechowujący czas pierwszego wykrycia każdego obiektu.
        last_seen (dict): Słownik przechowujący czas ostatniego wykrycia każdego obiektu.
    """

    def __init__(self, input_duration_threshold, output_duration_threshold):
        self.input_duration_threshold = input_duration_threshold
        self.output_duration_threshold = output_duration_threshold
        self.first_seen = {}
        self.last_seen = {}

    def update(self, detected_objects: list[EventObject]):
        """
        Aktualizuje tracker na podstawie listy wykrytych obiektów.

        Args:
            detected_objects (list[EventObject]): Lista obiektów wykrytych w bieżącym cyklu.
        """
        current_time = time.time()

        detected_object_ids = {obj.name_count_id for obj in detected_objects}

        # Aktualizacja czasu dla wykrytych obiektów
        for obj_id in detected_object_ids:
            if obj_id not in self.first_seen:
                self.first_seen[obj_id] = current_time
            self.last_seen[obj_id] = current_time

        # Usunięcie obiektów niewykrytych przez dłuższy czas
        for obj_id in list(self.last_seen.keys()):
            if (current_time - self.last_seen[obj_id] > self.output_duration_threshold
                    and obj_id not in detected_object_ids):
                del self.first_seen[obj_id]
                del self.last_seen[obj_id]

    def get_stable_objects(self) -> list[str]:
        """
        Zwraca listę identyfikatorów obiektów, które są uznane za stabilne.

        Returns:
            list[str]: Lista identyfikatorów stabilnych obiektów.
        """
        stable_objects = []
        current_time = time.time()
        for obj_id, first_seen_time in self.first_seen.items():
            if current_time - first_seen_time >= self.input_duration_threshold:
                if current_time - self.last_seen[obj_id] <= self.output_duration_threshold:
                    stable_objects.append(obj_id)
                    logging.debug(
                        f"Object ID '{obj_id}' is stable. Detected for {current_time - first_seen_time:.2f} seconds.")
                else:
                    logging.debug(
                        f"Object ID '{obj_id}' was last seen {current_time - self.last_seen[obj_id]:.2f} seconds ago.")
            else:
                logging.debug(
                    f"Object ID '{obj_id}' is not stable yet. Detected for {current_time - first_seen_time:.2f} seconds.")
        return stable_objects

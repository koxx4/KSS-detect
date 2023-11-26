import unittest
import time

from event_object import EventObject
from object_tracker import ObjectTracker


class TestObjectTracker(unittest.TestCase):

    def setUp(self):
        self.tracker = ObjectTracker(input_duration_threshold=3, output_duration_threshold=3)
        self.object1 = EventObject("Object1", 1, 0.9)
        self.object2 = EventObject("Object2", 2, 0.8)

    def test_object_should_not_be_considered_stable_immediately_after_being_detected(self):
        # Given
        self.tracker.update([self.object1])
        time.sleep(self.tracker.input_duration_threshold - 1)

        # When
        stable_objects = self.tracker.get_stable_objects()

        # Then
        self.assertNotIn(self.object1.name_count_id, stable_objects)

    def test_object_should_be_considered_stable_after_sufficient_time(self):
        # Given
        self.tracker.update([self.object1])
        time.sleep(self.tracker.input_duration_threshold - 1)
        self.tracker.update([self.object1])
        time.sleep(self.tracker.input_duration_threshold - 1)

        # When
        stable_objects = self.tracker.get_stable_objects()

        # Then
        self.assertIn(self.object1.name_count_id, stable_objects)

    def test_object_should_be_removed_if_not_detected_for_sufficient_time(self):
        # Given
        self.tracker.update([self.object1])
        time.sleep(self.tracker.input_duration_threshold + 1)
        self.tracker.update([])
        time.sleep(self.tracker.output_duration_threshold + 1)

        # When
        stable_objects = self.tracker.get_stable_objects()

        # Then
        self.assertNotIn(self.object1.name_count_id, stable_objects)


if __name__ == '__main__':
    unittest.main()

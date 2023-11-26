from event import KssEvent


class EventChangeDetector:
    def __init__(self):
        self.last_event: KssEvent | None = None

    def has_changed(self, event: KssEvent) -> bool:
        """Sprawdza, czy obecne zdarzenie różni się od ostatniego zapisanego zdarzenia."""

        current_event_ids = event.object_ids
        last_event_ids = self.last_event.object_ids if self.last_event else {}

        self.last_event = event

        return current_event_ids != last_event_ids

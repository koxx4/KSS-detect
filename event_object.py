class EventObject:
    def __init__(self, name: str, count: int, avg_confidence: float):
        self.name = name
        self.count = count
        self.avg_confidence = avg_confidence

    @property
    def name_count_id(self):
        return f"{self.name}-{self.count}"

    def __dict__(self) -> dict:
        return {
            "name": self.name,
            "count": self.count,
            "avg_confidence": self.avg_confidence,
            "ncid": self.name_count_id
        }

    def __str__(self):
        return f"{self.name}: {self.count}, ncid: {self.name_count_id}"

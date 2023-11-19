from datetime import datetime, timezone


class KssEvent:

    def __init__(self,
                 name: str,
                 count: int,
                 image: bytes,
                 confidence: float,
                 date=None,
                 important=False,
                 bounding_boxes=None):
        self.name = name
        self.count = count
        self.bounding_boxes = bounding_boxes
        self.image = image
        self.confidence = confidence
        self.date = date if date is not None else datetime.now(tz=timezone.utc)
        self.important = important

    def __str__(self):
        bounding_boxes_str = ', '.join(f"({x}, {y}, {w}, {h})" for x, y, w, h in (self.bounding_boxes or []))
        image_shape = self.image if self.image is not None else "None"
        return (f"DetectedObject(\n"
                f"  Name: {self.name}\n"
                f"  Count: {self.count}\n"
                f"  Bounding Boxes: [{bounding_boxes_str}]\n"
                f"  Image Shape: {image_shape}\n"
                f"  Confidence: {self.confidence:.2f}\n"
                f"  Date: {self.date}\n"
                f"  Important: {self.important}\n)")

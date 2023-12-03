class KssEventConfig:
    def __init__(self, event_name: str, precision_threshold: float, important=False):
        self.event_name = event_name
        self.precision_threshold = precision_threshold
        self.important = important


class KssSettings:
    def __init__(self, system_on: bool, input_threshold: int, output_threshold: int, events_config: [KssEventConfig]):
        self.system_on = system_on
        self.input_threshold = input_threshold
        self.output_threshold = output_threshold
        self.events_config = events_config

class MirAIeTopic:
    control_topic: str
    status_topic: str
    connection_status_topic: str

    def __init__(
        self, control_topic: str, status_topic: str, connection_status_topic: str
    ):
        self.control_topic = control_topic
        self.status_topic = status_topic
        self.connection_status_topic = connection_status_topic

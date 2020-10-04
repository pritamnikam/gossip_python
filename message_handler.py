class MessageHandler:
    def __init__(self):
        self.gossip_service = None
        self.logger = None

    def handle_new_message(self, envolope_in):
        pass

    def set_service(self, gossip_service):
        self.gossip_service = gossip_service

    def set_logger(self, logger):
        self.logger = logger

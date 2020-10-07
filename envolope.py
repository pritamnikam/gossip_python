import member_address

class MessageEnvolopeIn:
    def __init__(self, buffer, sender):
        self.sender = sender
        self.buffer = buffer


class MessageEnvolopeOut:
    def __init__(self,
                 sequence_number,
                 buffer,
                 max_attempts,
                 recipient):
        self.sequence_num = sequence_number
        self.attempt_num = 0
        self.attempt_ts = 0
        self.buffer = buffer
        self.recipient = recipient
        self.max_attempts = max_attempts

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

def test():
    a = member_address.Address()
    a.ip = '127.0.0.1'
    a.port = 8080

    buffer = bytes(f'abcd', 'utf-8')
    inbox = MessageEnvolopeIn(buffer, a)
    print(inbox.sender.to_string())
    print(inbox.sender.to_multiaddr())

    outbox = MessageEnvolopeOut(100, buffer, 5, a)
    print(outbox.recipient.to_string())
    print(outbox.recipient.to_multiaddr())

# test()
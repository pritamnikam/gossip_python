import config
import member
import vector_clock

MESSAGE_HELLO_TYPE = 0x01
MESSAGE_WELCOME_TYPE = 0x02
MESSAGE_MEMBER_LIST_TYPE = 0x03
MESSAGE_ACK_TYPE = 0x04
MESSAGE_DATA_TYPE = 0x05
MESSAGE_STATUS_TYPE = 0x06

MESSAGE_MIN_SIZE = 8
MESSAGE_MAX_SIZE = 1024

class Message:
    def __init__(self, message_type, sequence_num):
        self.message_type = message_type
        self.reserved = 0
        self.sequence_num = sequence_num

    def decode(self, buffer):
        self.message_type = int(buffer[:2].decode(config.FORMAT).strip()) # 2-byte
        self.reserved = int(buffer[2:4].decode(config.FORMAT).strip())    # 2-bytes
        self.sequence_num = int(buffer[4:8].decode(config.FORMAT).strip()) # 4-bytes
        return 2 + 2 + 4

    def encode(self):
        encoded_message_type = bytes(f'{self.message_type:>02}', config.FORMAT)  # 2-byte
        encoded_reserved = bytes(f'{self.reserved:>02}', config.FORMAT)          # 2-byte
        encoded_sequence_num = bytes(f'{self.sequence_num:>04}', config.FORMAT)  # 4-byte
        return encoded_message_type + encoded_reserved + encoded_sequence_num

    def destroy(self):
        pass
    
class Hello(Message):
    def __init__(self, message_type, sequence_num):
        Message.__init__(self, message_type, sequence_num)
        self.this_member = member.Member()

    def encode(self):
        encoded_message = Message.encode(self)
        encoded_member = self.this_member.encode()
        return encoded_message + encoded_member

    def decode(self, message):
        bytes_decoded = Message.decode(self, message)
        self.this_member = member.Member()
        bytes_decoded += self.this_member.decode(message[bytes_decoded:])
        return bytes_decoded

class Welcome(Message):
    def __init__(self, message_type, sequence_num):
        Message.__init__(self, message_type, sequence_num)
        self.hello_sequence_num = 0
        self.this_member = None

    def encode(self):
        encoded_message = Message.encode(self)
        encoded_sequence_num = bytes(f'{self.hello_sequence_num:>04}', config.FORMAT)  # 4-byte
        encoded_member = self.this_member.encode()
        return encoded_message + encoded_sequence_num + encoded_member

    def decode(self, buffer):
        bytes_decoded = Message.decode(self, buffer)
        self.hello_sequence_num = int(buffer[bytes_decoded:bytes_decoded+4].decode(config.FORMAT).strip()) # 4-bytes
        bytes_decoded += 4
        self.this_member = member.Member()
        bytes_decoded += self.this_member.decode(buffer[bytes_decoded:])
        return bytes_decoded

class MemberList(Message):
    def __init__(self, message_type, sequence_num):
        Message.__init__(self, message_type, sequence_num)
        self.members_n = 0
        self.members = []

    def encode(self):
        encoded_message = Message.encode(self)
        encoded_members_n = bytes(f'{self.members_n:>04}', config.FORMAT)  # 4-byte
        encoded_composit_message = encoded_message + encoded_members_n
        for member in self.members:
            encoded_message = member.encode()
            encoded_composit_message += encoded_message
        
        return encoded_composit_message

    def decode(self, buffer):
        bytes_decoded = Message.decode(self, buffer)
        self.members_n = int(buffer[bytes_decoded:bytes_decoded+4].decode(config.FORMAT).strip()) # 4-bytes
        
        offset = bytes_decoded + 4
        for i in range(self.members_n):
            member = member.Member()
            offset += member.decode(buffer[offset:])
            self.members.append(member)
        
        return offset

class Ack(Message):
    def __init__(self,message_type, sequence_num):
        Message.__init__(self, message_type, sequence_num)
        self.ack_sequence_num = 0

    def encode(self):
        encoded_message = Message.encode(self)
        encoded_ack_sequence_num = bytes(f'{self.ack_sequence_num:>04}', config.FORMAT)  # 4-byte
        return encoded_message + encoded_ack_sequence_num

    def decode(self, buffer):
        bytes_decoded = Message.decode(self, buffer)
        self.ack_sequence_num = int(buffer[bytes_decoded:].decode(config.FORMAT).strip()) # 4-bytes
        return bytes_decoded + 4

class Data(Message):
    def __init__(self, message_type, sequence_num):
        Message.__init__(self, message_type, sequence_num)
        self.data_version = vector_clock.VectorClock()
        self.data_size = 0
        self.data = b''

    def encode(self):
        encoded_message = Message.encode(self)
        encoded_data_version = self.data_version.encode()
        encoded_data_size = bytes(f'{self.data_size:>04}', config.FORMAT)  # 4-byte
        encoded_data = bytes(f'{self.data}', config.FORMAT)  # 4-byte
        return encoded_message + encoded_data_version + encoded_data_size + encoded_data

    def decode(self, buffer):
        bytes_decoded = Message.decode(self, buffer)
        self.data_version = vector_clock.VectorClock()
        bytes_decoded += self.data_version.decode(buffer[bytes_decoded:])

        self.data_size = int(buffer[bytes_decoded:bytes_decoded+4].decode(config.FORMAT).strip()) # 4-bytes
        self.data = buffer[bytes_decoded+4:].decode(config.FORMAT)
        return bytes_decoded + 4 + self.data_size

class Status(Message):
    def __init__(self, message_type, sequence_num):
        Message.__init__(self, message_type, sequence_num)
        self.data_version = vector_clock.VectorClock()

    def encode(self):
        encoded_message = Message.encode(self)
        encoded_data_version = self.data_version.encode()
        return encoded_message + encoded_data_version

    def decode(self, buffer):
        bytes_decoded = Message.decode(self, buffer)
        self.data_version = vector_clock.VectorClock()
        bytes_decoded += self.data_version.decode(buffer[bytes_decoded:])
        return bytes_decoded

class MessageFactory:
    def __init__(self):
        pass

    def create(self, message_type, sequence_number):
        if message_type == MESSAGE_HELLO_TYPE:
            return Hello(message_type, sequence_number)
        if message_type == MESSAGE_WELCOME_TYPE:
            return Welcome(message_type, sequence_number)
        if message_type == MESSAGE_ACK_TYPE:
            return Ack(message_type, sequence_number)

def test():
    msg = Hello(MESSAGE_HELLO_TYPE, 10)
    encoded_msg = msg.encode()

    test = Hello(0, 0)
    bytes_decoded = test.decode(encoded_msg)

    print(f"{len(encoded_msg)} and decode: {bytes_decoded}, test.type: {test.message_type}, sequence_num: {test.sequence_num}")

    m = member.Member()
    encoded_msg = m.encode()

    t = member.Member()
    bytes_decoded = t.decode(encoded_msg)
    print(f"{len(encoded_msg)} and decode: {bytes_decoded}")

    status = Status(MESSAGE_STATUS_TYPE, 10)
    encoded_msg = status.encode()

    st = Status(0, 0)
    bytes_decoded = st.decode(encoded_msg)
    print(f"{len(encoded_msg)} and decode: {bytes_decoded}")

    x = MemberList(MESSAGE_MEMBER_LIST_TYPE, 100)
    encoded_msg = x.encode()
    
    y = MemberList(0, 0)
    bytes_decoded = y.decode(encoded_msg)
    print(f"{len(encoded_msg)} and decode: {bytes_decoded}")


# test()

def decode_type(buffer, buffer_size):
    if (buffer_size < MESSAGE_MIN_SIZE):
        return False

    return int(buffer[:2].decode(config.FORMAT).strip()) # 2-byte

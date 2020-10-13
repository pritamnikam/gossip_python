import config
import util

class Address:
    def __init__(self):
        self.ip = ''
        self.port = 0

    def equals(self, other):
        return self.ip == other.ip and self.port == other.port

    def copy(self, other):
        self.ip = other.ip
        self.port = other.port

    def encode(self):
        multi_addr = self.to_multiaddr()
        encoded_addr = bytes(f'{multi_addr}', config.FORMAT)
        encoded_addr_length = bytes(f'{len(encoded_addr):>04}', config.FORMAT)   # 4-bytes
        composit_encoded_message = encoded_addr_length + encoded_addr
        return composit_encoded_message

    def decode(self, buffer):
        addr_length = int(buffer[:4].decode(config.FORMAT).strip()) # 4-bytes
        multi_addr = buffer[4:addr_length+4].decode(config.FORMAT)  # addr_length-bytes
        address = Address.from_multiaddr(multi_addr)
        self.ip = address.ip
        self.port = address.port
        return addr_length + 4

    def to_string(self):
        return f'{self.ip}:{self.port}'

    def to_multiaddr(self):
        return f'/ip4/{self.ip}/udp/{self.port}'

    def port_number(self):
        return self.ip
    
    def ip_address(self):
        return {self.ip}

    @staticmethod
    def from_string(address):
        try:
            split_list = address.split(':')
            if len(split_list) !=2  or not util.is_valid_ip_address(split_list[0]):
                return False

            addr = Address()    
            addr.ip = split_list[0]
            addr.port = int(split_list[1].strip())
            return addr
        except:
            return False

    @staticmethod
    def from_multiaddr(address):
        try:
            split_list = address.split('/')
            if len(split_list) != 5 or not util.is_valid_ip_address(split_list[2]):
                return False
            
            addr = Address()    
            addr.ip = split_list[2]
            addr.port = int(split_list[4].strip())
            return addr
        except Exception as e:
            print('Exception', str(e))
            return False

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
        return f'/ip/{self.ip}/port/{self.port}'

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


def test():
    addr = Address()
    addr.ip = '127.0.0.1'
    addr.port = 8080

    print(addr.to_string())
    print(addr.to_multiaddr())

    a = Address.from_string(addr.to_string())
    print(a.to_multiaddr())

    b = Address.from_multiaddr(addr.to_multiaddr())
    print(b.to_string())

    encoded_addr = addr.encode()

    c = Address()
    decoded_bytes = c.decode(encoded_addr)

    print(f'{len(encoded_addr)} and {decoded_bytes} -> {c.to_string()}')


# test()
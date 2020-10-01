import re

import config

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
        encoded_addr_length = bytes(f'{len(multi_addr):>04}', config.FORMAT)   # 4-bytes
        encoded_addr = bytes(f'{multi_addr}', config.FORMAT)
        return encoded_addr_length + encoded_addr

    def decode(self, buffer):
        addr_length = int(buffer[:4].decode(config.FORMAT).strip()) # 4-bytes
        multi_addr = buffer[4:addr_length+4].decode(config.FORMAT)  # addr_length-bytes
        address = from_multiaddr(multi_addr)
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

def validate_ip(ip):
    pat = re.compile("\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}")
    return pat.match(ip)

def from_string(address):
    try:
        split_list = address.split(':')
        if len(split_list) !=2  or not validate_ip(split_list[0]):
            return False

        addr = Address()    
        addr.ip = split_list[0]
        addr.port = int(split_list[1].strip())
        return addr
    except:
        return False

def from_multiaddr(address):
    try:
        split_list = address.split('/')
        if len(split_list) != 5 or not validate_ip(split_list[2]):
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

    a = from_string(addr.to_string())
    print(a.to_multiaddr())

    b = from_multiaddr(addr.to_multiaddr())
    print(b.to_string())

    encoded_addr = addr.encode()

    c = Address()
    decoded_bytes = c.decode(encoded_addr)

    print(f'{len(encoded_addr)} and {decoded_bytes} -> {c.to_string()}')


# test()